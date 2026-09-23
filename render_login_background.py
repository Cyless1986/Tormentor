"""Build a seamless, silent cinemagraph from Tormentor's original illustration."""
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
FFMPEG = Path(r'C:\Users\dwhd1\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.2-full_build\bin\ffmpeg.exe')
W, H, FPS, SECONDS = 1280, 720, 24, 12

def main():
    base = np.asarray(Image.open(ROOT/'assets/login-tavern.png').convert('RGB').resize((W,H), Image.Resampling.LANCZOS), dtype=np.float32)
    y,x = np.mgrid[0:H,0:W].astype(np.float32)
    x/=W; y/=H
    rng=np.random.default_rng(71)
    textures=[]
    for size in ((24,12),(48,24)):
        noise=Image.fromarray(rng.integers(0,256,(size[1],size[0]),dtype=np.uint8)).resize((W,H),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(15))
        textures.append(np.asarray(noise,dtype=np.float32)/255)
    # Match lanterns/windows in the source image; the architecture stays still.
    glow=np.zeros((H,W),dtype=np.float32)
    for cx,cy,sx,sy in ((.080,.13,.027,.043),(.055,.46,.032,.055),(.872,.715,.020,.026),(.735,.19,.017,.035)):
        glow+=np.exp(-((x-cx)/sx)**2-((y-cy)/sy)**2)
    lanterns=[]
    for cx,cy in ((.236,.283),(.185,.516),(.056,.438)):
        flame=np.exp(-((x-cx)/.007)**2-((y-cy)/.018)**2)
        wall=np.exp(-((x-cx)/.027)**2-((y-cy)/.040)**2)
        lanterns.append((flame+.28*wall)[...,None])
    mistmask=np.exp(-((y-.58)/.13)**2)*np.clip((x-.20)*4,0,1)
    skymask=np.clip((.35-y)*8,0,1)*np.clip((x-.25)*5,0,1)
    output=ROOT/'assets/login-tavern-loop-render.mp4'
    command=[str(FFMPEG),'-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    with subprocess.Popen(command,stdin=subprocess.PIPE,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)) as process:
        for frame in range(FPS*SECONDS):
            phase=2*np.pi*frame/(FPS*SECONDS)
            drift=np.roll(textures[0],int(W*frame/(FPS*SECONDS)),axis=1)
            slow=np.roll(textures[1],-int(W*frame/(FPS*SECONDS)),axis=1)
            alpha=(np.maximum(drift-.30,0)*.21+np.maximum(slow-.4,0)*.11)*mistmask
            cloud=np.maximum(drift-.36,0)*.075*skymask
            opacity=(alpha+cloud)[...,None]
            image=base*(1-opacity)+np.array([152,177,182],dtype=np.float32)*opacity
            flicker=0.48+0.21*np.sin(phase*7)+0.16*np.sin(phase*13+.8)+0.1*np.sin(phase*23)
            image+=glow[...,None]*flicker*np.array([28,13,3],dtype=np.float32)
            for index, lantern in enumerate(lanterns):
                offset=index*1.9
                light=.55+.24*np.sin(phase*5+offset)+.14*np.sin(phase*11+offset)+.07*np.sin(phase*19-offset)
                image+=lantern*light*np.array([92,52,13],dtype=np.float32)
            process.stdin.write(np.clip(image,0,255).astype(np.uint8).tobytes())
        process.stdin.close()
        if process.wait(): raise RuntimeError('FFmpeg encoding failed')
    output.replace(ROOT/'assets/login-tavern-loop.mp4')
    print('Login animation updated successfully',flush=True)

if __name__=='__main__': main()
