package com.jarvis.assistant

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import com.jarvis.assistant.audio.SpeechManager
import com.jarvis.assistant.data.OperatingMode
import com.jarvis.assistant.service.JarvisVoiceService
import com.jarvis.assistant.ui.screens.DashboardScreen
import com.jarvis.assistant.ui.screens.DeviceMeshScreen
import com.jarvis.assistant.ui.screens.MemoryVaultScreen
import com.jarvis.assistant.ui.screens.TaskCenterScreen
import com.jarvis.assistant.ui.theme.*
import com.jarvis.assistant.viewmodel.JarvisViewModel

class MainActivity : ComponentActivity() {

    private val viewModel: JarvisViewModel by viewModels()
    private var speechManager: SpeechManager? = null

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val recordAudioGranted = permissions[Manifest.permission.RECORD_AUDIO] ?: false
        if (recordAudioGranted) {
            JarvisVoiceService.startService(this)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize voice synthesizer
        speechManager = SpeechManager(
            context = this,
            onSpeechRecognized = { text -> viewModel.sendUserMessage(text) },
            onListeningStateChanged = { isListening -> viewModel.toggleVoiceListening() }
        )
        viewModel.speechCallback = { textToSpeak ->
            speechManager?.speak(textToSpeak)
        }

        checkAndRequestPermissions()

        setContent {
            JarvisTheme {
                MainAppScaffold(viewModel = viewModel)
            }
        }
    }

    private fun checkAndRequestPermissions() {
        val permissionsToRequest = mutableListOf(Manifest.permission.RECORD_AUDIO)
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            permissionsToRequest.add(Manifest.permission.POST_NOTIFICATIONS)
        }

        val missing = permissionsToRequest.filter {
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED
        }

        if (missing.isNotEmpty()) {
            permissionLauncher.launch(missing.toTypedArray())
        } else {
            JarvisVoiceService.startService(this)
        }
    }

    override fun onDestroy() {
        speechManager?.destroy()
        super.onDestroy()
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainAppScaffold(viewModel: JarvisViewModel) {
    var selectedTab by remember { mutableStateOf(0) }
    var showSettingsDialog by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        "J.A.R.V.I.S.",
                        color = NeonCyan,
                        fontSize = 18.sp,
                        letterSpacing = 2.sp
                    )
                },
                actions = {
                    IconButton(onClick = { showSettingsDialog = true }) {
                        Icon(
                            Icons.Default.Settings,
                            contentDescription = "Settings",
                            tint = NeonCyan
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = DarkSurface,
                    titleContentColor = NeonCyan
                )
            )
        },
        bottomBar = {
            NavigationBar(
                containerColor = DarkSurface,
                contentColor = NeonCyan
            ) {
                NavigationBarItem(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    icon = { Icon(Icons.Default.RecordVoiceOver, contentDescription = "HUD") },
                    label = { Text("HUD", fontSize = 11.sp) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = NeonCyan,
                        selectedTextColor = NeonCyan,
                        unselectedIconColor = TextMuted,
                        unselectedTextColor = TextMuted,
                        indicatorColor = DarkSurfaceElevated
                    )
                )
                NavigationBarItem(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    icon = { Icon(Icons.Default.DeveloperBoard, contentDescription = "Tasks") },
                    label = { Text("Tasks", fontSize = 11.sp) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = NeonCyan,
                        selectedTextColor = NeonCyan,
                        unselectedIconColor = TextMuted,
                        unselectedTextColor = TextMuted,
                        indicatorColor = DarkSurfaceElevated
                    )
                )
                NavigationBarItem(
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 },
                    icon = { Icon(Icons.Default.Psychology, contentDescription = "Memory") },
                    label = { Text("Memory", fontSize = 11.sp) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = NeonCyan,
                        selectedTextColor = NeonCyan,
                        unselectedIconColor = TextMuted,
                        unselectedTextColor = TextMuted,
                        indicatorColor = DarkSurfaceElevated
                    )
                )
                NavigationBarItem(
                    selected = selectedTab == 3,
                    onClick = { selectedTab = 3 },
                    icon = { Icon(Icons.Default.Hub, contentDescription = "Mesh") },
                    label = { Text("Mesh", fontSize = 11.sp) },
                    colors = NavigationBarItemDefaults.colors(
                        selectedIconColor = NeonCyan,
                        selectedTextColor = NeonCyan,
                        unselectedIconColor = TextMuted,
                        unselectedTextColor = TextMuted,
                        indicatorColor = DarkSurfaceElevated
                    )
                )
            }
        }
    ) { innerPadding ->
        Surface(modifier = Modifier.padding(innerPadding)) {
            when (selectedTab) {
                0 -> DashboardScreen(viewModel = viewModel)
                1 -> TaskCenterScreen(viewModel = viewModel)
                2 -> MemoryVaultScreen(viewModel = viewModel)
                3 -> DeviceMeshScreen(viewModel = viewModel)
            }
        }
    }

    if (showSettingsDialog) {
        SettingsDialog(viewModel = viewModel, onDismiss = { showSettingsDialog = false })
    }
}

@Composable
fun SettingsDialog(viewModel: JarvisViewModel, onDismiss: () -> Unit) {
    val settings = viewModel.settingsManager

    var apiKey by remember { mutableStateOf(settings.apiKey) }
    var selectedProvider by remember { mutableStateOf(settings.aiProvider) }
    var serverUrl by remember { mutableStateOf(settings.serverUrl) }
    var isStandalone by remember { mutableStateOf(settings.operatingMode == OperatingMode.STANDALONE_CLOUD) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text("JARVIS Core Settings", color = NeonCyan)
        },
        text = {
            Column(modifier = Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                Text(
                    "Architecture Mode:",
                    color = TextPrimary,
                    fontSize = 13.sp
                )
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        if (isStandalone) "Autonomous Cloud (No PC Needed)" else "Gateway Mesh (Connected to PC/Cloud)",
                        color = if (isStandalone) NeonCyan else WarningAmber,
                        fontSize = 12.sp
                    )
                    Switch(
                        checked = isStandalone,
                        onCheckedChange = { isStandalone = it }
                    )
                }

                OutlinedTextField(
                    value = apiKey,
                    onValueChange = { apiKey = it },
                    label = { Text("Cloud AI API Key (Groq / OpenAI)") },
                    singleLine = true,
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = NeonCyan,
                        unfocusedBorderColor = DarkSurfaceElevated,
                        focusedLabelColor = NeonCyan
                    )
                )

                if (!isStandalone) {
                    OutlinedTextField(
                        value = serverUrl,
                        onValueChange = { serverUrl = it },
                        label = { Text("Gateway Server URL") },
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = NeonCyan,
                            unfocusedBorderColor = DarkSurfaceElevated,
                            focusedLabelColor = NeonCyan
                        )
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    settings.apiKey = apiKey
                    settings.aiProvider = selectedProvider
                    settings.serverUrl = serverUrl
                    settings.operatingMode = if (isStandalone) OperatingMode.STANDALONE_CLOUD else OperatingMode.GATEWAY_MESH
                    if (!isStandalone) {
                        viewModel.connectGateway(serverUrl)
                    }
                    onDismiss()
                },
                colors = ButtonDefaults.buttonColors(containerColor = NeonCyan, contentColor = ObsidianBg)
            ) {
                Text("SAVE")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("CANCEL", color = TextMuted)
            }
        },
        containerColor = DarkSurface,
        textContentColor = TextPrimary
    )
}
