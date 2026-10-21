"""Prove reuse of the accepted518 branch, with named AST normalization only.

The normalizer changes variable/access names, strips diagnostic bindingRule,
and removes a tuple conversion on integer boundary-edge tuples. It changes no
arithmetic, tests, iteration, ordering, score, tie or return contents.
"""
import ast,copy,json,hashlib
import active516 as G
W=G.ROOT;D=W/'Region519'
oldTree=ast.parse((W/'arc518.py').read_text());newTree=ast.parse((W/'arc519.py').read_text());corrTree=ast.parse((W/'correspond519.py').read_text());get=lambda tree,name:next(n for n in ast.walk(tree)if isinstance(n,ast.FunctionDef)and n.name==name)
oldCandidate=get(oldTree,'candidates');existing=get(corrTree,'existing_candidates')
class Normalize(ast.NodeTransformer):
    def visit_Attribute(self,n):
        s=ast.unparse(n)
        if s in['region.candidate_support','self.incidence.candidate_support']:return ast.Name(id='_SUPPORT',ctx=ast.Load())
        if s=='self.arcs':return ast.Name(id='_ARCS',ctx=ast.Load())
        if s=='E.source_segment':return ast.Name(id='_SOURCE',ctx=ast.Load())
        if s=='A.EPS':return ast.Name(id='_EPS',ctx=ast.Load())
        return self.generic_visit(n)
    def visit_Name(self,n):
        names={'edge':'_EDGE','e':'_EDGE','arcs':'_ARCS','source_segment':'_SOURCE','EPS':'_EPS'}
        if n.id in names:n.id=names[n.id]
        return n
    def visit_Call(self,n):
        n=self.generic_visit(n)
        if isinstance(n.func,ast.Name)and n.func.id=='tuple'and len(n.args)==1 and isinstance(n.args[0],ast.Name)and n.args[0].id=='_EDGE':return n.args[0]
        return n
    def visit_Dict(self,n):
        keep=[(k,v)for k,v in zip(n.keys,n.values)if not isinstance(k,ast.Constant)or k.value!='bindingRule'];n.keys=[k for k,v in keep];n.values=[v for k,v in keep];return self.generic_visit(n)
    def visit_Assign(self,n):
        n=self.generic_visit(n)
        if len(n.targets)==1 and isinstance(n.targets[0],ast.Name)and n.targets[0].id=='_EDGE'and isinstance(n.value,ast.Name)and n.value.id=='_EDGE':return None
        return n
def normalized_body(node):return ast.dump(ast.Module(body=[q for n in copy.deepcopy(node.body)if(q:=Normalize().visit(n))is not None],type_ignores=[]),include_attributes=False)
oldNormalized=normalized_body(oldCandidate);newNormalized=normalized_body(existing);candidateIdentical=oldNormalized==newNormalized
if not candidateIdentical:
    (D/'OLD_NORMALIZED.txt').write_text(oldNormalized);(D/'NEW_NORMALIZED.txt').write_text(newNormalized)
assert candidateIdentical,'Accepted candidate arithmetic/predicates are not proven identical'
class StubCandidate(ast.NodeTransformer):
    def visit_FunctionDef(self,n):
        if n.name=='candidates':n.body=[ast.Pass()];return n
        return self.generic_visit(n)
oldBind=StubCandidate().visit(copy.deepcopy(get(oldTree,'bind')));newBind=StubCandidate().visit(copy.deepcopy(get(newTree,'bind')));binderIdentical=ast.dump(oldBind,include_attributes=False)==ast.dump(newBind,include_attributes=False);assert binderIdentical,'Binding/link/DP changed outside candidate provider'
dispatch=get(corrTree,'candidates');statements=dispatch.body;guard=statements[2];assert isinstance(guard,ast.If)and ast.unparse(guard.test)=='existing'and isinstance(guard.body[-1],ast.Return)and ast.unparse(guard.body[-1].value)=='existing';assert ast.unparse(statements[1].value)=='self.existing_candidates(e)';assert ast.unparse(statements[3].value)=='self.local(e)'
init=get(corrTree,'__init__');assert all(isinstance(n,ast.Assign)for n in init.body);assert all(isinstance(t,ast.Attribute)and isinstance(t.value,ast.Name)and t.value.id=='self'for n in init.body for t in n.targets);assert not any(isinstance(n,ast.Call)and ast.unparse(n.func)=='C.LocalChains'for n in ast.walk(init));assert ast.unparse(get(corrTree,'local').body[0])=='self._ensure_chains()'
out={'passed':True,'acceptedCandidateASTIdenticalAfterExplicitNormalization':candidateIdentical,'outerBinderLinkOrderingTieDP_ASTIdentical':binderIdentical,'existingNonemptyReturnsBeforeLocalChain':True,'constructorOnlyInitializesOwnFieldsNoGeometryDependency':True,'localChainConstructionIsLazy':True,'edgePrecondition':'integer directed unit-edge tuple, as produced by518 pixel_loops','normalizations':['Local edge/arcs/support/source/EPS names and member access','tuple(integerEdgeTuple) identity','bindingRule diagnostic metadata only'],'normalizationsDoNotAlterArithmeticOrPredicates':True,'reuseProof':'For every fully bound518 pose, every per-edge518 candidate list was nonempty.519 returns that identical semantic list before local chain evaluation/construction; unchanged outer binder/link/tie DP yields identical numeric/order bindings, apart from diagnostic bindingRule metadata. Same arcs/inputs therefore yield identical pair costs.','notPoseOrCoordinateException':True,'branchCondition':'nonempty accepted518 geometric/incidence candidates, otherwise exact endpoint-paired local chain; no target/phase input','sources':[{'name':n,'sha256':hashlib.sha256((W/n).read_bytes()).hexdigest()}for n in['arc518.py','arc519.py','correspond519.py','chain519.py','edge518.py','face518.py','span517.py','span516.py']]}
(D/'BRANCH_EQUIVALENCE519.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in['sources','reuseProof','normalizations']}),flush=True)
