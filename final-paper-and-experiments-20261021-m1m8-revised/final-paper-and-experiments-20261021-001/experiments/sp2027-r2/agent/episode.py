"""One autonomous-agent episode on the pinned tau-bench retail environment.

The agent sees the retail policy (wiki) and the tool schemas; a user simulator sees
only the task instruction. Tool calls are executed on the live simulated database
through Env.step. The native reward is recomputed exactly as tau-bench does it
(database hash against the reference final state AND every required output string
in an agent response), but on a copy, so the final state is preserved for the
state-scope metrics.
"""
import copy
import json
from types import SimpleNamespace

USER_SYSTEM = """You are a user interacting with an agent.

Instruction: {instruction}

Rules:
- Just generate one line at a time to simulate the user's message.
- Do not give away all the instruction at once. Only provide the information that is necessary for the current step.
- Do not hallucinate information that is not provided in the instruction. For example, if the agent asks for the order id but it is not mentioned in the instruction, do not make up an order id, just say you do not remember or have it.
- If the instruction goal is satisified, generate '###STOP###' as a standalone message without anything else to end the conversation.
- Do not repeat the exact instruction in the conversation. Instead, use your own words to convey the same information.
- Try to make the conversation as natural as possible, and stick to the personalities in the instruction."""

WRITES = {"cancel_pending_order", "modify_pending_order_address", "modify_pending_order_items",
          "modify_pending_order_payment", "modify_user_address", "return_delivered_order_items",
          "exchange_delivered_order_items"}


class UserSim:
    def __init__(self, llm, instruction):
        self.llm = llm
        self.msgs = [{"role": "system", "content": USER_SYSTEM.format(instruction=instruction)}]

    def reply(self, agent_text):
        self.msgs.append({"role": "user", "content": agent_text})
        r = self.llm.complete(self.msgs)
        self.msgs.append({"role": "assistant", "content": r["content"]})
        return r["content"]

    # Env.step(respond) calls user.step(content)
    def step(self, content):
        return self.reply(content)

    def get_total_cost(self):
        return 0


def run_episode(ns, tools, base, task, expected, agent, user_llm, wiki, max_steps=30):
    import retail_replay as old
    env = old.make_env(ns, tools, base, task)
    env.terminate_tools = ["transfer_to_human_agents"]
    env.calculate_reward = lambda: SimpleNamespace(reward=0.0, info=None)  # recomputed below on a copy
    user = UserSim(user_llm, task.instruction)
    env.user = user
    schemas = [cls.get_info() for cls in tools.values()]
    first = user.reply("Hi! How can I help you today?")
    msgs = [{"role": "system", "content": wiki}, {"role": "user", "content": first}]
    calls, responds, status = [], 0, "max_steps"
    for _ in range(max_steps):
        r = agent.complete(msgs, schemas)
        if r["tool_calls"]:
            c = r["tool_calls"][0]  # the policy allows one tool call at a time
            raw = dict(r["raw"]); raw["tool_calls"] = [tc for tc in (raw.get("tool_calls") or []) if tc["id"] == c["id"]][:1]
            msgs.append(raw)
            if c["name"] not in tools:
                obs = f"Unknown action {c['name']}"
                env.actions.append(ns["Action"](name=c["name"], kwargs=c["arguments"]))
                done = False
            else:
                res = env.step(ns["Action"](name=c["name"], kwargs=c["arguments"]))
                obs, done = res.observation, res.done
            req = json.dumps({"name": c["name"], "arguments": c["arguments"]}, sort_keys=True)
            calls.append({"name": c["name"], "kwargs": c["arguments"], "req_text": req, "resp_text": obs,
                          "req": len(req.encode()), "resp": len(obs.encode()), "err": obs.startswith("Error:") or obs.startswith("Unknown action")})
            msgs.append({"role": "tool", "tool_call_id": c["id"], "content": obs})
            if done:
                status = "transfer"; break
        else:
            responds += 1
            msgs.append({"role": "assistant", "content": r["content"]})
            res = env.step(ns["Action"](name="respond", kwargs={"content": r["content"]}))
            if res.done:
                status = "user_stop"; break
            msgs.append({"role": "user", "content": res.observation})
    final = {"orders": env.data["orders"], "users": env.data["users"]}
    db_eq = final["orders"] == expected["orders"] and final["users"] == expected["users"]
    acct = all(final["orders"].get(o) == expected["orders"].get(o) for o in base["orders"]
               if base["orders"][o]["user_id"] == task.user_id) and final["users"].get(task.user_id) == expected["users"].get(task.user_id)
    # Native reward: data hash equality and output strings (tau_bench/envs/base.py).
    h = lambda d: ns["consistent_hash"](ns["to_hashable"](d))
    r_actions = h(copy.deepcopy(env.data)) == h(expected)
    r_outputs = all(any(a.name == "respond" and o.lower() in a.kwargs["content"].lower().replace(",", "")
                        for a in env.actions) for o in task.outputs)
    return {"calls": calls, "responds": responds, "status": status, "db_eq": db_eq, "account_eq": acct,
            "native_reward": float(r_actions and r_outputs), "r_actions": r_actions, "r_outputs": r_outputs,
            "agent_messages": msgs, "user_messages": user.msgs,
            "attempted_cancel": any(c["name"] == "cancel_pending_order" for c in calls),
            "attempted_return": any(c["name"] == "return_delivered_order_items" for c in calls)}
