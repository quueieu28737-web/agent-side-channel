# GLM third-model replication

Requested alias: `glm-5.3-flash`. No immutable revision has been supplied.
The user supplied a dedicated server certificate after the initial trusted-chain
failure. TLS verification and a task-free native tool-call probe then passed;
the returned model is `glm-5.3-flash`. The protocol and analysis sources were
frozen before formal collection. Credentials and the dedicated CA file are
stored outside Git; the key is protected by Windows current-user DPAPI.

The planned comparison matches the R11 second-model design: 115 original
retail tasks, standard prompt, one episode each; 69 training and 46 test tasks
from 29 and 24 disjoint customers. Training-only calibration is frozen before
test collection. Both undefended and joint-program interventions are captured
as local TLS replays of the actual model decisions. The write-only and
write-removed diagnostic retains the ciphertext observable and fixed learners.

The compatibility receipt in `interface-probe/verification.json` records the
returned model, native-tool support and CA SHA256. The probe is excluded from
formal episodes. Never disable TLS verification or reuse R11 model responses.

`launch.ps1` reads the private `glm.json` and `glm.credential.xml` settings
under `LOCALAPPDATA/AgentSideChannelResearch`. An optional `ca_bundle` field
points to a user-verified CA file and is passed as `GLM_CA_BUNDLE` only to the
child process. `finish_analysis.py` then performs frozen evaluation and checks.
The launcher requires the frozen-ready protocol and keeps TLS validation enabled.
