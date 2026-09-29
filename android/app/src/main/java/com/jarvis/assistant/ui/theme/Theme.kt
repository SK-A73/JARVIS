package com.jarvis.assistant.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val DarkColorScheme = darkColorScheme(
    primary = NeonCyan,
    secondary = ElectricBlue,
    tertiary = WarningAmber,
    background = ObsidianBg,
    surface = DarkSurface,
    onPrimary = ObsidianBg,
    onSecondary = ObsidianBg,
    onBackground = TextPrimary,
    onSurface = TextPrimary
)

@Composable
fun JarvisTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content
    )
}
