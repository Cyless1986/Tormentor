package de.tormentor.app;

import android.content.Context;
import android.widget.VideoView;

/** Fill the home panel without changing the aspect ratio of the artwork. */
final class BackgroundVideoView extends VideoView {
    private int cropWidth, cropHeight;
    BackgroundVideoView(Context context) { super(context); }
    void setCropSize(int width,int height) {
        cropWidth=width;cropHeight=height;requestLayout();
    }
    @Override protected void onMeasure(int widthSpec,int heightSpec) {
        int width=MeasureSpec.getSize(widthSpec),height=MeasureSpec.getSize(heightSpec);
        if(cropWidth>0 && cropHeight>0 && width>0 && height>0) {
            double scale=Math.max((double)width/cropWidth,(double)height/cropHeight);
            setMeasuredDimension((int)Math.ceil(cropWidth*scale),(int)Math.ceil(cropHeight*scale));
        } else super.onMeasure(widthSpec,heightSpec);
    }
}
