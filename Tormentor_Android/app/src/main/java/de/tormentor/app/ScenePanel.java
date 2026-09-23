package de.tormentor.app;

import android.content.Context;
import android.view.View;
import android.widget.FrameLayout;

/** Keep controls inside the artwork's frame, including when the background is cropped. */
final class ScenePanel extends FrameLayout {
    private int left,top,width,height;
    ScenePanel(Context context){super(context);}
    @Override protected void onMeasure(int ws,int hs){
        int w=MeasureSpec.getSize(ws),h=MeasureSpec.getSize(hs);
        float scale=Math.max(w/960f,h/720f),dx=(w-960*scale)/2,dy=(h-720*scale)/2;
        int margin=Math.round(12*getResources().getDisplayMetrics().density);
        float density=getResources().getDisplayMetrics().density;
        if(ScreenLayout.useFullSceneArea(Math.round(w/density),Math.round(h/density))){
            // A cropped tablet artwork must never squeeze phone controls off screen.
            left=Math.min(margin,w/4);top=Math.min(margin,h/4);
            width=Math.max(1,w-2*left);height=Math.max(1,h-2*top);
            setMeasuredDimension(w,h);
            for(int i=0;i<getChildCount();i++)getChildAt(i).measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.EXACTLY));
            return;
        }
        left=Math.max(margin,Math.round(dx+230*scale));
        top=Math.max(margin,Math.round(dy+105*scale));
        int right=Math.min(w-margin,Math.round(dx+835*scale));
        int bottom=Math.min(h-margin,Math.round(dy+550*scale));
        width=Math.max(1,right-left);height=Math.max(1,bottom-top);
        setMeasuredDimension(w,h);
        for(int i=0;i<getChildCount();i++)getChildAt(i).measure(MeasureSpec.makeMeasureSpec(width,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(height,MeasureSpec.EXACTLY));
    }
    @Override protected void onLayout(boolean changed,int l,int t,int r,int b){
        for(int i=0;i<getChildCount();i++){View child=getChildAt(i);child.layout(left,top,left+width,top+height);}
    }
}
