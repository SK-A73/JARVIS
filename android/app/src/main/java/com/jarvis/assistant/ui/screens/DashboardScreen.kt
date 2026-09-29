package com.jarvis.assistant.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.jarvis.assistant.ui.components.OrbState
import com.jarvis.assistant.ui.components.OrbVisualizer
import com.jarvis.assistant.ui.theme.*
import com.jarvis.assistant.viewmodel.ChatMessage
import com.jarvis.assistant.viewmodel.JarvisViewModel

@Composable
fun DashboardScreen(viewModel: JarvisViewModel) {
    val isOnline by viewModel.isOnline.collectAsState()
    val orbState by viewModel.orbState.collectAsState()
    val statusText by viewModel.statusText.collectAsState()
    val messages by viewModel.messages.collectAsState()

    var textInput by remember { mutableStateOf("") }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ObsidianBg)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Top Status Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "J.A.R.V.I.S.",
                color = NeonCyan,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
            Surface(
                color = if (isOnline) DarkSurfaceElevated else CriticalCrimson.copy(alpha = 0.2f),
                shape = RoundedCornerShape(12.dp)
            ) {
                Text(
                    text = if (isOnline) "● ONLINE" else "○ OFFLINE",
                    color = if (isOnline) NeonCyan else CriticalCrimson,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Medium,
                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                )
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Futuristic Orb Visualizer
        OrbVisualizer(
            state = orbState,
            size = 140.dp
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Status Subtitle
        Text(
            text = statusText,
            color = TextSecondary,
            fontSize = 13.sp,
            fontWeight = FontWeight.Normal
        )

        Spacer(modifier = Modifier.height(16.dp))

        // Chat Conversation Stream
        LazyColumn(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp),
            reverseLayout = true
        ) {
            items(messages.reversed()) { msg ->
                ChatBubble(msg)
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Interactive Input Bar
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically
        ) {
            OutlinedTextField(
                value = textInput,
                onValueChange = { textInput = it },
                placeholder = { Text("Ask JARVIS or give a command...", color = TextMuted) },
                modifier = Modifier.weight(1f),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = NeonCyan,
                    unfocusedBorderColor = DarkSurfaceElevated,
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary
                ),
                shape = RoundedCornerShape(24.dp),
                maxLines = 3
            )

            Spacer(modifier = Modifier.width(8.dp))

            // Send Button
            IconButton(
                onClick = {
                    if (textInput.isNotBlank()) {
                        viewModel.sendUserMessage(textInput)
                        textInput = ""
                    }
                },
                modifier = Modifier
                    .background(DarkSurfaceElevated, CircleShape)
                    .size(48.dp)
            ) {
                Icon(Icons.Default.Send, contentDescription = "Send", tint = NeonCyan)
            }

            Spacer(modifier = Modifier.width(6.dp))

            // Voice Mic Toggle
            IconButton(
                onClick = { viewModel.toggleVoiceListening() },
                modifier = Modifier
                    .background(if (orbState == OrbState.LISTENING) WarningAmber else NeonCyan, CircleShape)
                    .size(48.dp)
            ) {
                Icon(Icons.Default.Mic, contentDescription = "Voice", tint = ObsidianBg)
            }
        }
    }
}

@Composable
fun ChatBubble(message: ChatMessage) {
    val isUser = message.sender == "user"
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Surface(
            color = if (isUser) ElectricBlue.copy(alpha = 0.25f) else DarkSurface,
            shape = RoundedCornerShape(16.dp),
            border = if (!isUser) androidx.compose.foundation.BorderStroke(1.dp, NeonCyan.copy(alpha = 0.2f)) else null,
            modifier = Modifier.widthIn(max = 280.dp)
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                if (!isUser) {
                    Text(
                        text = "JARVIS (${message.emotion})",
                        color = NeonCyan,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                }
                Text(
                    text = message.text,
                    color = TextPrimary,
                    fontSize = 14.sp
                )
            }
        }
    }
}
