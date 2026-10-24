"""Defense-aware learners with fixed hyperparameters; no test-label tuning."""
from r7common import *
from sklearn.feature_extraction import DictVectorizer
from sklearn.ensemble import RandomForestClassifier,ExtraTreesClassifier,GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
import torch
from torch import nn
torch.set_num_threads(1)
torch.use_deterministic_algorithms(True)

def feature(r):
    f=features(r['records'],'joint');recs=np.array(r['records'],float).reshape(-1,3)
    if len(recs):
        cum=np.r_[0,np.cumsum(recs[:,0]*recs[:,1])]
        for i,v in enumerate(np.interp(np.linspace(0,len(recs),100),np.arange(len(cum)),cum)):f['cum_'+str(i)]=float(v)
        runs=[]
        for d,n,t in recs:
            if runs and runs[-1][0]==d:runs[-1][1]+=1;runs[-1][2]+=n
            else:runs.append([d,1,n])
        for i,(d,c,b) in enumerate(runs[:64]):f['burst_dir_'+str(i)]=d;f['burst_count_'+str(i)]=c;f['burst_bytes_'+str(i)]=b
    return f

class LeafKNN:
    """k-FP-style leaf fingerprint distance, not the original feature implementation."""
    def fit(self,X,y):
        self.vec=DictVectorizer(sparse=False);a=self.vec.fit_transform(X)
        self.forest=RandomForestClassifier(n_estimators=200,min_samples_leaf=2,class_weight='balanced',random_state=SEED,n_jobs=1).fit(a,y)
        self.leaves=self.forest.apply(a);self.y=np.array(y);return self
    def predict_proba(self,X):
        leaf=self.forest.apply(self.vec.transform(X));scores=[]
        for l in leaf:
            dist=np.mean(l!=self.leaves,axis=1);idx=np.argsort(dist,kind='stable')[:3];scores.append(float(self.y[idx].mean()))
        s=np.array(scores);return np.c_[1-s,s]

def sequence(rows,L=512):
    a=np.zeros((len(rows),4,L),np.float32);truncated=0
    for i,r in enumerate(rows):
        x=np.array(r['records'],float).reshape(-1,3)
        if not len(x):continue
        gaps=np.maximum(0,np.diff(x[:,2],prepend=x[0,2])/1e6)
        # Absolute, label-independent scaling; gaps are computed before head/tail selection.
        z=np.stack((x[:,0],np.log2(x[:,1]+1)/16,np.log1p(gaps)/8,np.ones(len(x))),axis=0)
        if len(x)>L:z=np.c_[z[:,:L//2],z[:,-L//2:]];truncated+=1
        a[i,:,:z.shape[1]]=z
    return torch.from_numpy(a),truncated

class CNN(nn.Module):
    def __init__(self):
        super().__init__();self.conv=nn.Sequential(nn.Conv1d(4,16,7,padding=3),nn.ReLU(),nn.MaxPool1d(2),
            nn.Conv1d(16,32,5,padding=2),nn.ReLU())
        self.head=nn.Linear(64,1)
    def forward(self,x):
        z=self.conv(x);return self.head(torch.cat((z.mean(-1),z.amax(-1)),1)).flatten()

class SequenceAttack:
    def fit(self,rows,y):
        torch.manual_seed(SEED);self.model=CNN();a,self.train_truncated=sequence(rows)
        target=torch.tensor(y,dtype=torch.float32);pos=max(1,float(target.sum()));neg=len(y)-pos
        loss=nn.BCEWithLogitsLoss(pos_weight=torch.tensor(neg/pos));opt=torch.optim.Adam(self.model.parameters(),lr=.001,weight_decay=.0001)
        gen=torch.Generator().manual_seed(SEED)
        self.losses=[]
        for epoch in range(50):
            total=0.;self.model.train()
            for idx in torch.randperm(len(y),generator=gen).split(32):
                opt.zero_grad();v=loss(self.model(a[idx]),target[idx]);v.backward();opt.step();total+=float(v.detach())*len(idx)
            self.losses.append(total/len(y))
        self.model.eval();return self
    def predict_proba(self,rows):
        x,_=sequence(rows)
        with torch.no_grad():s=torch.sigmoid(self.model(x)).numpy()
        return np.c_[1-s,s]

def tabular():return {
    'D2_logistic':make_pipeline(DictVectorizer(sparse=False),StandardScaler(),LogisticRegression(C=1,class_weight='balanced',max_iter=5000,random_state=SEED)),
    'D2_gradient_boosting':make_pipeline(DictVectorizer(sparse=False),GradientBoostingClassifier(n_estimators=100,random_state=SEED)),
    'D2_random_forest':make_pipeline(DictVectorizer(sparse=False),RandomForestClassifier(n_estimators=200,min_samples_leaf=2,class_weight='balanced',random_state=SEED,n_jobs=1)),
    'D2_extra_trees':make_pipeline(DictVectorizer(sparse=False),ExtraTreesClassifier(n_estimators=200,min_samples_leaf=2,class_weight='balanced',random_state=SEED,n_jobs=1)),
    'D2_leaf_fingerprint':LeafKNN()}
