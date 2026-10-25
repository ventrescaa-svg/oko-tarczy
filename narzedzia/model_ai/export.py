# Użycie: python3 export.py model.pt ../../model/grot.onnx   (sprawdza też zgodność z PyTorch)
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np, sys
src = open(__import__('os').path.join(__import__('os').path.dirname(__file__), 'train.py')).read()
exec(src[src.index('class Net'):src.index('def batch')].replace("F.interpolate(a, size=b.shape[2:], mode='bilinear', align_corners=False)", "F.interpolate(a, scale_factor=2.0, mode='bilinear', align_corners=False)"))
net = Net(); net.load_state_dict(torch.load(sys.argv[1])); net.eval()
class Wrap(nn.Module):
    def __init__(s, n): super().__init__(); s.n = n
    def forward(s, x): return s.n(x)
x = torch.zeros(1, 9, 256, 384)
torch.onnx.export(Wrap(net), x, sys.argv[2], input_names=['x'], output_names=['heat'], opset_version=13, dynamo=True, do_constant_folding=True)
import onnx, onnxruntime as ort, os
m = onnx.load(sys.argv[2])
if os.environ.get('OPSET'): m = onnx.version_converter.convert_version(m, int(os.environ['OPSET']))
onnx.save(m, sys.argv[2], save_as_external_data=False)
if os.path.exists(sys.argv[2] + '.data'): os.remove(sys.argv[2] + '.data')
m = onnx.load(sys.argv[2]); print(sorted(set(n.op_type for n in m.graph.node)))
xr = torch.rand(1, 9, 256, 384)
a = net(xr).detach().numpy(); b = ort.InferenceSession(sys.argv[2]).run(None, {'x': xr.numpy()})[0]
print('max diff', np.abs(a - b).max(), 'skala', np.abs(a).max(), b.shape)
