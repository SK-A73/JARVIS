package com.jarvis.assistant.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews
import com.jarvis.assistant.MainActivity
import com.jarvis.assistant.R
import com.jarvis.assistant.service.JarvisVoiceService

class JarvisAppWidget : AppWidgetProvider() {

    companion object {
        const val ACTION_WIDGET_ACTIVATE = "com.jarvis.assistant.ACTION_WIDGET_ACTIVATE"
        const val ACTION_WIDGET_STOP = "com.jarvis.assistant.ACTION_WIDGET_STOP"

        fun updateAllWidgets(context: Context, status: String = "ONLINE", subtitle: String = "Tap to speak") {
            val appWidgetManager = AppWidgetManager.getInstance(context)
            val thisWidget = ComponentName(context, JarvisAppWidget::class.java)
            val allWidgetIds = appWidgetManager.getAppWidgetIds(thisWidget)
            for (widgetId in allWidgetIds) {
                updateAppWidget(context, appWidgetManager, widgetId, status, subtitle)
            }
        }

        private fun updateAppWidget(
            context: Context,
            appWidgetManager: AppWidgetManager,
            appWidgetId: Int,
            status: String,
            subtitle: String
        ) {
            val views = RemoteViews(context.packageName, R.layout.jarvis_widget_layout)

            views.setTextViewText(R.id.widget_title, "JARVIS • $status")
            views.setTextViewText(R.id.widget_status_text, subtitle)

            // Intent to activate voice listening directly
            val activateIntent = Intent(context, JarvisAppWidget::class.java).apply {
                action = ACTION_WIDGET_ACTIVATE
            }
            val activatePendingIntent = PendingIntent.getBroadcast(
                context,
                0,
                activateIntent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )

            // Intent to open Main UI
            val openAppIntent = Intent(context, MainActivity::class.java)
            val openAppPendingIntent = PendingIntent.getActivity(
                context,
                1,
                openAppIntent,
                PendingIntent.FLAG_IMMUTABLE
            )

            views.setOnClickPendingIntent(R.id.widget_root, openAppPendingIntent)
            views.setOnClickPendingIntent(R.id.widget_mic_btn, activatePendingIntent)

            appWidgetManager.updateAppWidget(appWidgetId, views)
        }
    }

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        for (appWidgetId in appWidgetIds) {
            updateAppWidget(context, appWidgetManager, appWidgetId, "ONLINE", "Tap to speak")
        }
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action == ACTION_WIDGET_ACTIVATE) {
            // Start Voice service and trigger microphone
            JarvisVoiceService.startService(context)
            val triggerVoiceIntent = Intent(context, JarvisVoiceService::class.java).apply {
                action = JarvisVoiceService.ACTION_TRIGGER_VOICE
            }
            context.startService(triggerVoiceIntent)
            updateAllWidgets(context, "LISTENING", "Yes, how can I help?")
        } else if (intent.action == ACTION_WIDGET_STOP) {
            JarvisVoiceService.stopService(context)
            updateAllWidgets(context, "STANDBY", "Tap to activate")
        }
    }
}
