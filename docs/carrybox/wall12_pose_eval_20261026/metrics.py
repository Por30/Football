"""Physical-unit pose diagnostics; deliberately independent of training losses."""
import torch


def measurements(pred, target, symmetries, allowed):
    pred, target, symmetries = pred.double(), target.double(), symmetries.double()
    delta = pred[:, :3] - target[:, :3]
    a, b = pred[:, 3:6], pred[:, 6:9]
    x = torch.nn.functional.normalize(a, dim=-1, eps=1.e-12)
    orthogonal = b - (x*b).sum(-1, keepdim=True)*x
    y = torch.nn.functional.normalize(orthogonal, dim=-1, eps=1.e-12)
    valid = (a.norm(dim=-1)>1.e-6) & (orthogonal.norm(dim=-1)>1.e-6)
    estimated = torch.stack((x,y,torch.linalg.cross(x,y)), -1)
    tx,ty = target[:,3:6],target[:,6:9]
    reference = torch.stack((tx,ty,torch.linalg.cross(tx,ty)), -1)
    candidates = reference[:,None] @ symmetries
    cosine = ((estimated[:,None]*candidates).sum((-1,-2))-1)/2
    angles = torch.rad2deg(cosine.clamp(-1,1).acos())
    folded = angles.masked_fill(~allowed,float('inf')).min(-1).values
    raw = torch.rad2deg((((estimated*reference).sum((-1,-2))-1)/2).clamp(-1,1).acos())
    rot6 = candidates[...,:2].transpose(-1,-2).flatten(-2)
    error = (pred[:,None,3:]-rot6).square().mean(-1)
    return dict(delta_m=delta, position_m=delta.norm(dim=-1),
                position_mse=delta.square().mean(-1), angle_valid=valid,
                angle_deg=folded, raw_angle_deg=raw,
                rotation6_mse=error.masked_fill(~allowed,float('inf')).min(-1).values)


def summarize(data, mask):
    count = int(mask.sum())
    if not count: return dict(frames=0)
    distance = data['position_m'][mask]*100
    valid = mask & data['angle_valid']
    result = dict(frames=count,position_mean_cm=float(distance.mean()),
        position_median_cm=float(distance.median()),position_p90_cm=float(distance.quantile(.9)),
        position_rmse_cm=float(distance.square().mean().sqrt()),
        axis_mae_cm=(data['delta_m'][mask].abs().mean(0)*100).tolist(),
        axis_bias_cm=(data['delta_m'][mask].mean(0)*100).tolist(),
        position_mse=float(data['position_mse'][mask].mean()),
        rotation6_mse=float(data['rotation6_mse'][mask].mean()),
        angle_valid_frames=int(valid.sum()),angle_degenerate_frames=count-int(valid.sum()))
    if valid.any():
        angles = data['angle_deg'][valid]
        result.update(angle_mean_deg=float(angles.mean()),angle_median_deg=float(angles.median()),
            angle_p90_deg=float(angles.quantile(.9)),raw_angle_mean_deg=float(data['raw_angle_deg'][valid].mean()))
    return result
