package com.jarvis.assistant

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build

class JarvisApplication : Application() {

    companion object {
        const val CHANNEL_VOICE_SESSION_ID = "jarvis_voice_session_channel"
        const val CHANNEL_TASKS_ID = "jarvis_tasks_channel"
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

            // Foreground Voice Service Channel (Low vibration, ongoing)
            val voiceChannel = NotificationChannel(
                CHANNEL_VOICE_SESSION_ID,
                getString(R.string.channel_voice_service_name),
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = getString(R.string.channel_voice_service_desc)
                setShowBadge(false)
            }

            // High Priority Channel for Task completions and approvals
            val taskChannel = NotificationChannel(
                CHANNEL_TASKS_ID,
                getString(R.string.channel_tasks_name),
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = getString(R.string.channel_tasks_desc)
                enableVibration(true)
            }

            notificationManager.createNotificationChannel(voiceChannel)
            notificationManager.createNotificationChannel(taskChannel)
        }
    }
}
