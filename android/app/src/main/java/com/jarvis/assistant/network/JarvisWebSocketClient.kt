package com.jarvis.assistant.network

import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import okhttp3.*
import org.json.JSONObject
import java.util.concurrent.TimeUnit

interface JarvisWebSocketListener {
    fun onConnected()
    fun onDisconnected()
    fun onStatusReceived(status: String, message: String)
    fun onStreamStart(emotion: String, confidence: Float)
    fun onStreamChunk(chunk: String)
    fun onStreamEnd(fullText: String, emotion: String)
    fun onChatResponse(content: String, emotion: String)
    fun onError(error: String)
}

class JarvisWebSocketClient(
    private val serverUrl: String,
    private val clientId: String,
    private val listener: JarvisWebSocketListener
) {
    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()

    private var webSocket: WebSocket? = null
    private val scope = CoroutineScope(Dispatchers.IO)
    private var isManuallyClosed = false
    private var reconnectAttempts = 0

    fun connect() {
        isManuallyClosed = false
        val url = "$serverUrl/ws/client/$clientId"
        val request = Request.Builder().url(url).build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(ws: WebSocket, response: Response) {
                reconnectAttempts = 0
                listener.onConnected()
            }

            override fun onMessage(ws: WebSocket, text: String) {
                handleIncomingMessage(text)
            }

            override fun onClosing(ws: WebSocket, code: Int, reason: String) {
                ws.close(1000, null)
                listener.onDisconnected()
            }

            override fun onFailure(ws: WebSocket, t: Throwable, response: Response?) {
                listener.onError(t.localizedMessage ?: "WebSocket failure")
                listener.onDisconnected()
                scheduleReconnect()
            }
        })
    }

    private fun handleIncomingMessage(text: String) {
        try {
            val json = JSONObject(text)
            when (json.optString("type")) {
                "jarvis_status" -> {
                    listener.onStatusReceived(
                        json.optString("state", "online"),
                        json.optString("message", "")
                    )
                }
                "stream_start" -> {
                    listener.onStreamStart(
                        json.optString("inferred_emotion", "Calm"),
                        json.optDouble("confidence", 0.8).toFloat()
                    )
                }
                "stream_chunk" -> {
                    listener.onStreamChunk(json.optString("chunk", ""))
                }
                "stream_end" -> {
                    val emo = json.optJSONObject("emotion")?.optString("state") ?: "Calm"
                    listener.onStreamEnd(json.optString("full_text", ""), emo)
                }
                "chat_response" -> {
                    val emo = json.optJSONObject("emotion")?.optString("state") ?: "Calm"
                    listener.onChatResponse(json.optString("content", ""), emo)
                }
            }
        } catch (e: Exception) {
            Log.e("JarvisWS", "Error parsing incoming frame", e)
        }
    }

    fun sendMessage(text: String) {
        val payload = JSONObject().apply {
            put("message", text)
        }
        webSocket?.send(payload.toString())
    }

    private fun scheduleReconnect() {
        if (isManuallyClosed) return
        scope.launch {
            val backoffSeconds = minOf(30, 2 shl minOf(reconnectAttempts, 4))
            reconnectAttempts++
            delay(backoffSeconds * 1000L)
            connect()
        }
    }

    fun disconnect() {
        isManuallyClosed = true
        webSocket?.close(1000, "User disconnected")
    }
}
