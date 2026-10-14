"""Vector errors on each sample exactly once; root-frame position and world velocity in root axes."""
import torch


@torch.no_grad()
def ball_prediction_metrics(policy, observations, chunk_size=2048):
    # Caller supplies a flat batch, including action-time status when available.
    n = observations.batch_size[0]
    errors, statuses, visibility = [], [], []
    for start in range(0, n, chunk_size):
        obs = observations[start:start + chunk_size]
        errors.append((policy.predict_ball_state(obs) - obs[policy.privileged_group]).detach())
        if 'ball_status' in obs:
            statuses.append(obs['ball_status'].bool())
            # Agile's synthetic depth is noise-free, far=3 m; newest history entry is last.
            visibility.append(obs['perception'][:, -1].flatten(1).amin(-1) < 3. - 1.e-5)
    err = torch.cat(errors)
    groups = {'all': torch.ones(n, dtype=torch.bool, device=err.device)}
    if statuses:
        status, visible = torch.cat(statuses), torch.cat(visibility)
        groups.update(active=status[:, 0], visible=visible, active_visible=status[:, 0] & visible,
                      incoming=status[:, 1], near_foot=status[:, 2])
    result = {'mse': err.square().mean().item()}
    for name, mask in groups.items():
        count = int(mask.sum())
        result[f'{name}/count'] = count
        result[f'{name}/fraction'] = count / n
        if not count:  # Deliberately absent errors: no samples are not zero error.
            continue
        for label, part, scale in [('position_cm', err[mask, :3], 100.), ('velocity_m_s', err[mask, 3:], 1.)]:
            norms = part.norm(dim=-1) * scale
            result[f'{name}/{label}_rmse'] = norms.square().mean().sqrt().item()
            result[f'{name}/{label}_p95'] = torch.quantile(norms, .95).item()
    return result
