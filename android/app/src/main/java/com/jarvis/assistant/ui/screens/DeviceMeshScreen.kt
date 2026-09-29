package com.jarvis.assistant.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.jarvis.assistant.ui.theme.*
import com.jarvis.assistant.viewmodel.JarvisViewModel
import com.jarvis.assistant.viewmodel.UiDevice

@Composable
fun DeviceMeshScreen(viewModel: JarvisViewModel) {
    val devices by viewModel.devices.collectAsState()

    // Default preview list if none synced yet
    val displayDevices = if (devices.isEmpty()) {
        listOf(
            UiDevice("android_phone", "Android Client (This Phone)", "phone", true, listOf("mic", "speaker", "hud")),
            UiDevice("laptop_win11", "Windows Laptop Node", "laptop", true, listOf("terminal", "filesystem", "build")),
            UiDevice("jarvis_cloud", "JARVIS 24/7 Gateway", "server", true, listOf("memory", "llm", "tasks"))
        )
    } else devices

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ObsidianBg)
            .padding(16.dp)
    ) {
        Text(
            text = "Multi-Device Mesh Topology",
            color = NeonCyan,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = "Active execution nodes and capability routing",
            color = TextMuted,
            fontSize = 12.sp
        )

        Spacer(modifier = Modifier.height(16.dp))

        LazyColumn(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            items(displayDevices) { dev ->
                DeviceCard(device = dev)
            }
        }
    }
}

@Composable
fun DeviceCard(device: UiDevice) {
    Surface(
        color = DarkSurface,
        shape = RoundedCornerShape(12.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, DarkSurfaceElevated),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(14.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = device.name,
                    color = TextPrimary,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold
                )
                Text(
                    text = if (device.isOnline) "● ONLINE" else "○ OFFLINE",
                    color = if (device.isOnline) NeonCyan else CriticalCrimson,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = "Type: ${device.type.uppercase()} • ID: ${device.id}",
                color = TextSecondary,
                fontSize = 11.sp
            )

            Spacer(modifier = Modifier.height(8.dp))
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                device.capabilities.forEach { cap ->
                    Surface(
                        color = DarkSurfaceElevated,
                        shape = RoundedCornerShape(4.dp)
                    ) {
                        Text(
                            text = cap,
                            color = TextSecondary,
                            fontSize = 10.sp,
                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                        )
                    }
                }
            }
        }
    }
}
