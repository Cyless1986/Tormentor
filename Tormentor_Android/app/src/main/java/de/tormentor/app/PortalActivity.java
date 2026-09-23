package de.tormentor.app;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/** Mobile view of the shared campaign portal; supports the same handout upload workflow as the website. */
public class PortalActivity extends Activity {
    private WebView view;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        view = new WebView(this);
        WebSettings settings = view.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setSupportZoom(false);
        view.setWebViewClient(new WebViewClient());
        view.loadUrl("https://tormentor-codex.de/login");
        setContentView(view);
    }
    @Override public void onBackPressed() {
        if (view != null && view.canGoBack()) view.goBack(); else super.onBackPressed();
    }
}
