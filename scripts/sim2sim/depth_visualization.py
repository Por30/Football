"""Render copies of the exact v4 policy depth input, without a GPU renderer."""
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from matplotlib import colormaps
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure


class LiveDepthWindow:
    """Nonblocking Tk window; closing it leaves the MuJoCo simulation running."""
    def __init__(self, speed=2.):
        import tkinter as tk
        from PIL import Image, ImageTk
        self.Image, self.ImageTk = Image, ImageTk
        self.root = tk.Tk()
        self.root.title('Kickball - Live policy depth')
        self.root.configure(bg='#f5f7fa')
        self.root.protocol('WM_DELETE_WINDOW',self.close)
        self.closed = False
        self.frames = 0
        self.commands = []
        self.cmap = colormaps['turbo_r']
        tk.Label(self.root,text='LIVE POLICY DEPTH  |  48 x 27  |  ray distance [m]',
                 font=('Sans',15,'bold'),bg='#f5f7fa').grid(row=0,column=0,columnspan=8,pady=10)
        self.latest = tk.Label(self.root,bg='#dce3eb')
        self.latest.grid(row=1,column=0,columnspan=5,padx=8)
        self.info = tk.Label(self.root,font=('Sans',12),justify='left',bg='#f5f7fa')
        self.info.grid(row=1,column=5,columnspan=3,padx=12,sticky='nw')
        legend = np.linspace(.1,3,640,dtype=np.float32)[None].repeat(14,axis=0)
        self.legend = tk.Label(self.root)
        self.legend.grid(row=2,column=0,columnspan=5,pady=(8,0))
        self._set_image(self.legend,legend,(640,14),mask_far=False)
        tk.Label(self.root,text='0.1 m (near)                                     3.0 m (far)',
                 bg='#f5f7fa').grid(row=3,column=0,columnspan=5)
        self.history = []
        for h in range(8):
            tk.Label(self.root,text=f't - {(7-h)*20} ms' if h<7 else 't / latest',bg='#f5f7fa').grid(row=4,column=h,pady=(12,0))
            label = tk.Label(self.root,bg='#dce3eb')
            label.grid(row=5,column=h,padx=3,pady=3)
            self.history.append(label)
        tk.Label(self.root,text='Grey: no hit (3 m). v4 analytic ball only; no ground/body occlusion.',
                 bg='#f5f7fa',fg='#765129').grid(row=6,column=0,columnspan=8,pady=10)
        controls = tk.LabelFrame(self.root,text='Ball speed [m/s]',bg='#f5f7fa',padx=10,pady=6)
        controls.grid(row=7,column=0,columnspan=8,sticky='ew',padx=8,pady=(0,10))
        self.speed_slider = tk.Scale(controls,from_=min(.1,speed),to=max(6.,speed),resolution=-1,
                                     orient='horizontal',length=360,bg='#f5f7fa',digits=3)
        self.speed_slider.set(speed)
        self.speed_slider.grid(row=0,column=0,rowspan=2)
        self.speed_slider.configure(command=lambda value: self.commands.append(('set',float(value))))
        self.apply_button = tk.Button(controls,text='Apply now',command=lambda: self._queue_speed('apply'))
        self.apply_button.grid(row=0,column=1,padx=10)
        self.serve_button = tk.Button(controls,text='Re-serve',command=lambda: self._queue_speed('serve'))
        self.serve_button.grid(row=0,column=2,padx=10)
        self.speed_info = tk.Label(controls,text=f'Serve: {speed:.2f} m/s',bg='#f5f7fa')
        self.speed_info.grid(row=1,column=1,columnspan=2)
        tk.Label(controls,text='Slider: next serve. Apply now: keep direction. Re-serve: reset ball only.',
                 bg='#f5f7fa').grid(row=2,column=0,columnspan=3,sticky='w')
        self.root.update_idletasks()

    def _queue_speed(self, action):
        self.commands.append((action,float(self.speed_slider.get())))

    def take_commands(self):
        commands, self.commands = self.commands, []
        return commands

    def update_speed(self, requested, measured):
        if not self.closed:
            self.speed_info.configure(text=f'Serve: {requested:.2f} m/s  |  Actual XY: {measured:.2f} m/s')

    def _set_image(self,label,depth,size,mask_far=True):
        rgb = (self.cmap(np.clip((depth-.1)/2.9,0,1))[:,:,:3]*255).astype(np.uint8)
        if mask_far:
            rgb[depth>=3] = [220,227,235]
        picture = self.Image.fromarray(rgb).resize(size,self.Image.Resampling.NEAREST)
        photo = self.ImageTk.PhotoImage(picture,master=self.root)
        label.configure(image=photo)
        label.image = photo

    def update(self,stack,time_s):
        if self.closed:
            return
        frame = stack[-1]
        self._set_image(self.latest,frame,(640,360))
        for label,depth in zip(self.history,stack):
            self._set_image(label,depth,(120,68))
        hits = frame < 3
        nearest = f'{frame[hits].min():.3f} m' if hits.any() else 'no hit'
        self.info.configure(text=f't = {time_s:.2f} s\n\nNearest hit: {nearest}\n\nHit pixels: {hits.sum()} / 1296\n\nPolicy: 50 Hz\nDisplay: 10 Hz\nHistory: 8 x 20 ms')
        self.frames += 1
        self.poll()

    def poll(self):
        if not self.closed:
            self.root.update_idletasks()
            self.root.update()

    def close(self):
        if not self.closed:
            self.closed = True
            self.root.destroy()


def export_depth_video(directory, samples, fps=10):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    times = np.asarray([t for t, _ in samples], dtype=np.float64)
    stacks = np.asarray([d for _, d in samples], dtype=np.float32)
    if stacks.ndim != 4 or stacks.shape[1:] != (8, 27, 48) or not np.isfinite(stacks).all():
        raise ValueError('Expected finite [frames,8,27,48] depth samples')
    if not len(times) or np.any(stacks < .1) or np.any(stacks > 3):
        raise ValueError('Empty or out-of-range v4 depth capture')
    if len(times) > 1 and not np.allclose(np.diff(times), 1/fps, atol=1e-8):
        raise ValueError('Video timestamps do not match requested frame rate')
    np.savez_compressed(directory/'depth_raw.npz', time_s=times, depth_m=stacks)
    current = stacks[:, -1]
    hits = current < 3
    counts = hits.sum(axis=(1,2))
    nearest = np.min(np.where(hits,current,np.inf),axis=(1,2))
    preview_index = int(np.argmax(counts))

    fig = Figure(figsize=(12,7), dpi=100, facecolor='#f5f7fa')
    canvas = FigureCanvasAgg(fig)
    fig.text(.045,.955,'KICKBALL / POLICY DEPTH',fontsize=20,weight='bold',color='#172b46')
    timestamp = fig.text(.955,.96,'',ha='right',fontsize=14,color='#172b46')
    fig.text(.045,.918,'Actual network input  |  48 x 27 pixels  |  distance along each ray [m]',
             fontsize=11,color='#52647a')
    cmap = colormaps['turbo_r'].copy()
    cmap.set_bad('#dce3eb')
    ax = fig.add_axes([.045,.33,.57,.55])
    image = ax.imshow(np.ma.masked_greater_equal(current[0],3),vmin=.1,vmax=3,
                      cmap=cmap,interpolation='nearest',origin='upper')
    ax.set_xlabel('pixel u')
    ax.set_ylabel('pixel v')
    ax.set_title('Latest frame',loc='left',fontsize=12)
    cax = fig.add_axes([.635,.36,.016,.46])
    bar = fig.colorbar(image,cax=cax,ticks=[.1,.5,1,1.5,2,2.5,3])
    bar.set_label('ray distance [m]',fontsize=10)
    info = fig.text(.745,.79,'',fontsize=13,color='#172b46',linespacing=1.4,va='top')
    fig.text(.745,.405,'Grey = no ray hit\n(stored value: 3.0 m)',fontsize=11,color='#52647a')
    fig.text(.745,.30,'v4 analytic sphere depth\nGround / body occlusion absent',fontsize=10,color='#765129')
    fig.text(.045,.245,'8-FRAME INPUT HISTORY  /  oldest to newest, 20 ms per step',fontsize=11,weight='bold',color='#172b46')
    history_images = []
    for h in range(8):
        ha = fig.add_axes([.045+h*.116,.10,.108,.115])
        history_images.append(ha.imshow(np.ma.masked_greater_equal(stacks[0,h],3),vmin=.1,vmax=3,
                                        cmap=cmap,interpolation='nearest',origin='upper'))
        ha.set_xticks([])
        ha.set_yticks([])
        ha.set_title(f't - {(7-h)*20} ms' if h < 7 else 't / latest',fontsize=9)
    fig.text(.045,.035,'Fixed colour scale; nearest-pixel display. History repeats the first frame after a reset.',
             fontsize=10,color='#52647a')
    video = directory/'depth.mp4'
    with imageio.get_writer(video,format='FFMPEG',mode='I',fps=fps,codec='libx264',
                            quality=7,macro_block_size=2,ffmpeg_params=['-threads','1']) as writer:
        for i,stack in enumerate(stacks):
            image.set_data(np.ma.masked_greater_equal(stack[-1],3))
            for artist,frame in zip(history_images,stack):
                artist.set_data(np.ma.masked_greater_equal(frame,3))
            timestamp.set_text(f't = {times[i]:05.2f} s')
            near_text = f'{nearest[i]:.3f} m' if counts[i] else 'no hit'
            info.set_text(f'Nearest hit\n{near_text}\n\nHit pixels\n{counts[i]} / 1296  ({counts[i]/1296:.1%})\n\nPolicy / video\n50 Hz / {fps} fps')
            canvas.draw()
            writer.append_data(np.asarray(canvas.buffer_rgba())[:,:,:3].copy())
            if i == preview_index:
                fig.savefig(directory/'depth_preview.png',dpi=100,facecolor=fig.get_facecolor())
    # Decode metadata/count, rather than treating a created file as a valid video.
    with imageio.get_reader(video,format='FFMPEG') as reader:
        decoded_frames = reader.count_frames()
        video_meta = reader.get_meta_data()
    if decoded_frames != len(times):
        raise RuntimeError(f'Video has {decoded_frames} frames, expected {len(times)}')
    result = {'frames':len(times),'video_fps':fps,'video_duration_s':len(times)/fps,
              'video_size':list(video_meta['size']),'decoded_frames':decoded_frames,
              'raw_shape':list(stacks.shape),'policy_hz':50,'history_step_s':.02,
              'sampled_visible_frames':int(np.count_nonzero(counts)),
              'preview_time_s':float(times[preview_index]),'preview_hit_pixels':int(counts[preview_index]),
              'min_hit_depth_m':float(nearest.min()) if hits.any() else None,
              'depth_semantics':'v4 analytic ball-only ray distance in metres; 3m=no hit',
              'video':'depth.mp4','preview':'depth_preview.png','raw':'depth_raw.npz'}
    (directory/'depth_info.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
