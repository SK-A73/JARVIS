package com.jarvis.assistant.service

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.IBinder
import androidx.core.app.NotificationCompat
import com.jarvis.assistant.JarvisApplication
import com.jarvis.assistant.MainActivity
import com.jarvis.assistant.R
import com.jarvis.assistant.audio.SpeechManager
import com.jarvis.assistant.network.JarvisWebSocketClient
import com.jarvis.assistant.network.JarvisWebSocketListener

class JarvisVoiceService : Service(), JarvisWebSocketListener {

    companion object {
        const val ACTION_START_SESSION = "com.jarvis.assistant.START_SESSION"
        const val ACTION_STOP_SESSION = "com.jarvis.assistant.STOP_SESSION"
        const val ACTION_TRIGGER_VOICE = "com.jarvis.assistant.TRIGGER_VOICE"
        private const val NOTIFICATION_ID = 42001

        fun startService(context: Context) {
            val intent = Intent(context, JarvisVoiceService::class.java).apply {
                action = ACTION_START_SESSION
            }
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                context.startForegroundService(intent)
            } else {
                context.startService(intent)
            }
        }

        fun stopService(context: Context) {
            val intent = Intent(context, JarvisVoiceService::class.java).apply {
                action = ACTION_STOP_SESSION
            }
            context.startService(intent)
        }
    }

    private var speechManager: SpeechManager? = null
    private var webSocketClient: JarvisWebSocketClient? = null
    private var isSessionActive = false

    override fun onCreate() {
        super.onCreate()
        speechManager = SpeechManager(
            context = this,
            onSpeechRecognized = { recognizedText ->
                webSocketClient?.sendMessage(recognizedText)
            },
            onListeningStateChanged = { isListening ->
                updateNotification(if (isListening) "Listening to you..." else "Connected & Standby")
            }
        )

        // Local gateway endpoint (can be configured via shared preferences)
        webSocketClient = JarvisWebSocketClient(
            serverUrl = "ws://10.0.2.2:8000", // Android emulator host alias
            clientId = "android_phone_client",
            listener = this
        )
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP_SESSION -> {
                stopForeground(true)
                stopSelf()
                return START_NOT_STICKY
            }
            ACTION_TRIGGER_VOICE -> {
                speechManager?.startListening()
            }
            ACTION_START_SESSION -> {
                if (!isSessionActive) {
                    startForeground(NOTIFICATION_ID, buildNotification("JARVIS is active and listening."))
                    webSocketClient?.connect()
                    isSessionActive = true
                }
            }
        }
        return START_STICKY
    }

    private fun buildNotification(statusText: String): Notification {
        val openAppIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE
        )

        val stopIntent = PendingIntent.getService(
            this,
            1,
            Intent(this, JarvisVoiceService::class.java).apply { action = ACTION_STOP_SESSION },
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, JarvisApplication.CHANNEL_VOICE_SESSION_ID)
            .setContentTitle("JARVIS Personal Assistant")
            .setContentText(statusText)
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setContentIntent(openAppIntent)
            .setOngoing(true)
            .addAction(android.R.drawable.ic_menu_close_clear_cancel, "STOP", stopIntent)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun updateNotification(statusText: String) {
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as android.app.NotificationManager
        notificationManager.notify(NOTIFICATION_ID, buildNotification(statusText))
    }

    // --- WebSocket Callbacks ---
    override fun onConnected() {
        updateNotification("Online. Tap to speak or say command.")
    }

    override fun onDisconnected() {
        updateNotification("Reconnecting to JARVIS Core...")
    }

    override fun onStatusReceived(status: String, message: String) {
        updateNotification(message)
    }

    override fun onStreamStart(emotion: String, confidence: Float) {
        updateNotification("JARVIS is thinking...")
    }

    override fun onStreamChunk(chunk: String) {}

    override fun onStreamEnd(fullText: String, emotion: String) {
        updateNotification("Responding...")
        speechManager?.speak(fullText) {
            updateNotification("Online and Standby")
        }
    }

    override fun onChatResponse(content: String, emotion: String) {
        speechManager?.speak(content) {
            updateNotification("Online and Standby")
        }
    }

    override fun onError(error: String) {
        updateNotification("Network error: $error")
    }

    override fun onDestroy() {
        speechManager?.destroy()
        webSocketClient?.disconnect()
        isSessionActive = false
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
