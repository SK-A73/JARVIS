package com.jarvis.assistant.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.jarvis.assistant.data.OperatingMode
import com.jarvis.assistant.data.SettingsManager
import com.jarvis.assistant.network.DirectAiClient
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

class JarvisViewModel(application: Application) : AndroidViewModel(application), JarvisWebSocketListener {

    val settingsManager = SettingsManager(application)
    private val directAiClient = DirectAiClient(settingsManager)

    var speechCallback: ((String) -> Unit)? = null

    private val _isOnline = MutableStateFlow(true)
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

    init {
        // Welcome greeting
        val initialGreeting = if (settingsManager.operatingMode == OperatingMode.STANDALONE_CLOUD) {
            "JARVIS Autonomous Mobile Core initialized. Standing by for voice or text directives, ${settingsManager.userName}."
        } else {
            "JARVIS Gateway mesh mode initialized. Attempting connection to backend gateway..."
        }
        _messages.value = listOf(ChatMessage(sender = "jarvis", text = initialGreeting))

        if (settingsManager.operatingMode == OperatingMode.GATEWAY_MESH) {
            connectGateway(settingsManager.serverUrl)
        }
    }

    fun connectGateway(serverUrl: String) {
        wsClient?.disconnect()
        wsClient = JarvisWebSocketClient(serverUrl, "android_phone_ui", this)
        wsClient?.connect()
    }

    fun sendUserMessage(text: String) {
        if (text.isBlank()) return
        val userMsg = ChatMessage(sender = "user", text = text)
        _messages.value = _messages.value + userMsg

        if (settingsManager.operatingMode == OperatingMode.STANDALONE_CLOUD || wsClient == null || !_isOnline.value) {
            // Autonomous Direct Cloud Mode
            viewModelScope.launch {
                _orbState.value = OrbState.THINKING
                _statusText.value = "Consulting Cloud Neural Core..."
                val history = _messages.value.map { it.sender to it.text }
                val result = directAiClient.getCompletion(text, history)
                result.onSuccess { responseText ->
                    _orbState.value = OrbState.IDLE
                    _statusText.value = "Standby"
                    val jarvisMsg = ChatMessage(sender = "jarvis", text = responseText, emotion = "Calm")
                    _messages.value = _messages.value + jarvisMsg
                    speechCallback?.invoke(responseText)
                }.onFailure { err ->
                    _orbState.value = OrbState.IDLE
                    _statusText.value = "Standby"
                    val errMsg = ChatMessage(
                        sender = "jarvis",
                        text = "I encountered an issue: ${err.localizedMessage ?: err.message}",
                        emotion = "Concern"
                    )
                    _messages.value = _messages.value + errMsg
                    speechCallback?.invoke("Sir, I encountered an issue: ${err.localizedMessage ?: err.message}")
                }
            }
        } else {
            // Gateway Mesh Mode
            _orbState.value = OrbState.THINKING
            _statusText.value = "Analyzing intent via Gateway..."
            wsClient?.sendMessage(text)
        }
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
        _statusText.value = "Gateway Mesh Online"
    }

    override fun onDisconnected() {
        if (settingsManager.operatingMode == OperatingMode.GATEWAY_MESH) {
            _isOnline.value = false
            _statusText.value = "Gateway Offline - Direct Cloud Fallback Ready"
        }
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
        val finalText = fullText.ifEmpty { currentStreamingText.toString() }
        val jarvisMsg = ChatMessage(sender = "jarvis", text = finalText, emotion = emotion)
        _messages.value = _messages.value + jarvisMsg
        speechCallback?.invoke(finalText)
        currentStreamingText.clear()
    }

    override fun onChatResponse(content: String, emotion: String) {
        _orbState.value = OrbState.IDLE
        val jarvisMsg = ChatMessage(sender = "jarvis", text = content, emotion = emotion)
        _messages.value = _messages.value + jarvisMsg
        speechCallback?.invoke(content)
    }

    override fun onError(error: String) {
        _statusText.value = "Notice: $error"
    }

    override fun onCleared() {
        wsClient?.disconnect()
        super.onCleared()
    }
}
