package com.jarvis.assistant.data

import android.content.Context
import android.content.SharedPreferences

enum class OperatingMode {
    STANDALONE_CLOUD, // Independent mobile AI software (Zero laptop needed)
    GATEWAY_MESH      // Connected to JARVIS Gateway Server
}

class SettingsManager(context: Context) {
    private val prefs: SharedPreferences = context.getSharedPreferences("jarvis_prefs", Context.MODE_PRIVATE)

    companion object {
        private const val KEY_MODE = "operating_mode"
        private const val KEY_API_KEY = "ai_api_key"
        private const val KEY_AI_PROVIDER = "ai_provider" // "groq", "openai", "openrouter"
        private const val KEY_SERVER_URL = "gateway_server_url"
        private const val KEY_USER_NAME = "user_name"
    }

    var operatingMode: OperatingMode
        get() {
            val name = prefs.getString(KEY_MODE, OperatingMode.STANDALONE_CLOUD.name) ?: OperatingMode.STANDALONE_CLOUD.name
            return try { OperatingMode.valueOf(name) } catch (e: Exception) { OperatingMode.STANDALONE_CLOUD }
        }
        set(value) = prefs.edit().putString(KEY_MODE, value.name).apply()

    var apiKey: String
        get() = prefs.getString(KEY_API_KEY, "") ?: ""
        set(value) = prefs.edit().putString(KEY_API_KEY, value).apply()

    var aiProvider: String
        get() = prefs.getString(KEY_AI_PROVIDER, "groq") ?: "groq"
        set(value) = prefs.edit().putString(KEY_AI_PROVIDER, value).apply()

    var serverUrl: String
        get() = prefs.getString(KEY_SERVER_URL, "https://jarvis-ai-gateway.onrender.com") ?: "https://jarvis-ai-gateway.onrender.com"
        set(value) = prefs.edit().putString(KEY_SERVER_URL, value).apply()

    var userName: String
        get() = prefs.getString(KEY_USER_NAME, "Sir") ?: "Sir"
        set(value) = prefs.edit().putString(KEY_USER_NAME, value).apply()
}
