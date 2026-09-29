package com.jarvis.assistant.network

import com.jarvis.assistant.data.SettingsManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

class DirectAiClient(private val settingsManager: SettingsManager) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()

    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    suspend fun getCompletion(
        userMessage: String,
        history: List<Pair<String, String>> = emptyList()
    ): Result<String> = withContext(Dispatchers.IO) {
        val apiKey = settingsManager.apiKey.trim()
        val provider = settingsManager.aiProvider.lowercase()

        // Choose endpoint and model based on provider
        val (endpoint, model, effectiveKey) = when (provider) {
            "openai" -> Triple(
                "https://api.openai.com/v1/chat/completions",
                "gpt-4o-mini",
                apiKey
            )
            "openrouter" -> Triple(
                "https://openrouter.ai/api/v1/chat/completions",
                "meta-llama/llama-3.2-3b-instruct:free",
                apiKey
            )
            else -> Triple(
                "https://api.groq.com/openai/v1/chat/completions",
                "llama-3.3-70b-versatile",
                apiKey
            )
        }

        if (effectiveKey.isEmpty()) {
            return@withContext Result.failure(
                IllegalStateException("Cloud AI API key is not configured. Please tap Settings in the top bar to enter your free Groq or OpenAI key.")
            )
        }

        try {
            val root = JSONObject()
            root.put("model", model)

            val messagesArray = JSONArray()

            // System prompt
            val sysObj = JSONObject()
            sysObj.put("role", "system")
            sysObj.put(
                "content",
                "You are JARVIS, an autonomous personal AI assistant created for ${settingsManager.userName}. " +
                        "Be concise, highly capable, professional yet warm, with a touch of dry wit. " +
                        "Optimize responses for spoken audio output."
            )
            messagesArray.put(sysObj)

            // Conversation history (last 6 turns)
            for ((role, text) in history.takeLast(6)) {
                val msg = JSONObject()
                msg.put("role", if (role == "user") "user" else "assistant")
                msg.put("content", text)
                messagesArray.put(msg)
            }

            // Current user message
            val currentMsg = JSONObject()
            currentMsg.put("role", "user")
            currentMsg.put("content", userMessage)
            messagesArray.put(currentMsg)

            root.put("messages", messagesArray)
            root.put("temperature", 0.7)
            root.put("max_tokens", 512)

            val body = root.toString().toRequestBody(jsonMediaType)
            val request = Request.Builder()
                .url(endpoint)
                .addHeader("Authorization", "Bearer $effectiveKey")
                .addHeader("Content-Type", "application/json")
                .post(body)
                .build()

            val response = client.newCall(request).execute()
            if (!response.isSuccessful) {
                val errBody = response.body?.string() ?: "HTTP ${response.code}"
                return@withContext Result.failure(Exception("API Error (${response.code}): $errBody"))
            }

            val respString = response.body?.string() ?: ""
            val json = JSONObject(respString)
            val choices = json.getJSONArray("choices")
            if (choices.length() > 0) {
                val firstChoice = choices.getJSONObject(0)
                val content = firstChoice.getJSONObject("message").getString("content")
                Result.success(content)
            } else {
                Result.failure(Exception("No completion choices returned by model"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
