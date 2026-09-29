package com.jarvis.assistant.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.jarvis.assistant.network.JarvisWebSocketClient
import com.jarvis.assistant.network.JarvisWebSocketListener
import com.jarvis.assistant.ui.components.OrbState
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ChatMessage(
    val id: String = java.util.UUID.randomUUID().toString(),
    val sender: String, // "user" or "jarvis"
    val text: String,
    val emotion: String = "Calm",
    val timestamp: Long = System.currentTimeMillis()
)

data class UiTask(
    val id: String,
    val title: String,
    val status: String,
    val currentStep: String? = null
)

data class UiMemory(
    val id: String,
    val content: String,
    val category: String,
    val importance: Float
)

data class UiDevice(
    val id: String,
    val name: String,
    val type: String,
    val isOnline: Boolean,
    val capabilities: List<String>
)

class JarvisViewModel : ViewModel(), JarvisWebSocketListener {

    private val _isOnline = MutableStateFlow(false)
    val isOnline: StateFlow<Boolean> = _isOnline.asStateFlow()

    private val _orbState = MutableStateFlow(OrbState.IDLE)
    val orbState: StateFlow<OrbState> = _orbState.asStateFlow()

    private val _statusText = MutableStateFlow("All Systems Standby")
    val statusText: StateFlow<String> = _statusText.asStateFlow()

    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages: StateFlow<List<ChatMessage>> = _messages.asStateFlow()

    private val _tasks = MutableStateFlow<List<UiTask>>(emptyList())
    val tasks: StateFlow<List<UiTask>> = _tasks.asStateFlow()

    private val _memories = MutableStateFlow<List<UiMemory>>(emptyList())
    val memories: StateFlow<List<UiMemory>> = _memories.asStateFlow()

    private val _devices = MutableStateFlow<List<UiDevice>>(emptyList())
    val devices: StateFlow<List<UiDevice>> = _devices.asStateFlow()

    private var wsClient: JarvisWebSocketClient? = null
    private var currentStreamingText = StringBuilder()

    fun initConnection(serverUrl: String, clientId: String = "android_phone_ui") {
        wsClient = JarvisWebSocketClient(serverUrl, clientId, this)
        wsClient?.connect()
    }

    fun sendUserMessage(text: String) {
        if (text.isBlank()) return
        val userMsg = ChatMessage(sender = "user", text = text)
        _messages.value = _messages.value + userMsg
        _orbState.value = OrbState.THINKING
        _statusText.value = "Analyzing intent..."
        wsClient?.sendMessage(text)
    }

    fun toggleVoiceListening() {
        if (_orbState.value == OrbState.LISTENING) {
            _orbState.value = OrbState.IDLE
            _statusText.value = "Standby"
        } else {
            _orbState.value = OrbState.LISTENING
            _statusText.value = "Listening to you..."
        }
    }

    fun cancelActiveTask(taskId: String) {
        sendUserMessage("JARVIS, stop task $taskId")
    }

    fun deleteMemoryItem(memoryId: String) {
        _memories.value = _memories.value.filter { it.id != memoryId }
        sendUserMessage("JARVIS, delete memory $memoryId")
    }

    // --- WebSocket Callbacks ---
    override fun onConnected() {
        _isOnline.value = true
        _statusText.value = "Core Online"
    }

    override fun onDisconnected() {
        _isOnline.value = false
        _orbState.value = OrbState.IDLE
        _statusText.value = "Core Offline - Reconnecting..."
    }

    override fun onStatusReceived(status: String, message: String) {
        _statusText.value = message
    }

    override fun onStreamStart(emotion: String, confidence: Float) {
        _orbState.value = OrbState.SPEAKING
        _statusText.value = "JARVIS responding ($emotion)"
        currentStreamingText.clear()
    }

    override fun onStreamChunk(chunk: String) {
        currentStreamingText.append(chunk)
    }

    override fun onStreamEnd(fullText: String, emotion: String) {
        _orbState.value = OrbState.IDLE
        _statusText.value = "Standby"
        val jarvisMsg = ChatMessage(
            sender = "jarvis",
            text = fullText.ifEmpty { currentStreamingText.toString() },
            emotion = emotion
        )
        _messages.value = _messages.value + jarvisMsg
        currentStreamingText.clear()
    }

    override fun onChatResponse(content: String, emotion: String) {
        _orbState.value = OrbState.IDLE
        val jarvisMsg = ChatMessage(sender = "jarvis", text = content, emotion = emotion)
        _messages.value = _messages.value + jarvisMsg
    }

    override fun onError(error: String) {
        _statusText.value = "Network Notice: $error"
    }

    override fun onCleared() {
        wsClient?.disconnect()
        super.onCleared()
    }
}
