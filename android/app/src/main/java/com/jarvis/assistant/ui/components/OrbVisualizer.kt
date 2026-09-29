package com.jarvis.assistant.ui.components

import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.jarvis.assistant.ui.theme.ElectricBlue
import com.jarvis.assistant.ui.theme.NeonCyan
import com.jarvis.assistant.ui.theme.WarningAmber

enum class OrbState {
    IDLE, LISTENING, THINKING, SPEAKING
}

@Composable
fun OrbVisualizer(
    state: OrbState,
    modifier: Modifier = Modifier,
    size: Dp = 160.dp
) {
    val infiniteTransition = rememberInfiniteTransition(label = "orb_pulse")

    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.85f,
        targetValue = if (state == OrbState.LISTENING) 1.25f else 1.05f,
        animationSpec = infiniteRepeatable(
            animation = tween(
                durationMillis = when (state) {
                    OrbState.LISTENING -> 600
                    OrbState.THINKING -> 900
                    OrbState.SPEAKING -> 750
                    OrbState.IDLE -> 2000
                },
                easing = FastOutSlowInEasing
            ),
            repeatMode = RepeatMode.Reverse
        ),
        label = "scale"
    )

    val rotation by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = 360f,
        animationSpec = infiniteRepeatable(
            animation = tween(if (state == OrbState.THINKING) 1500 else 6000, easing = LinearEasing)
        ),
        label = "rotation"
    )

    val primaryColor = when (state) {
        OrbState.LISTENING -> NeonCyan
        OrbState.THINKING -> WarningAmber
        OrbState.SPEAKING -> ElectricBlue
        OrbState.IDLE -> NeonCyan.copy(alpha = 0.7f)
    }

    Box(
        modifier = modifier.size(size),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.size(size)) {
            val center = this.center
            val radius = (size.toPx() / 3f) * pulseScale

            // Outer Ripple Ring
            drawCircle(
                color = primaryColor.copy(alpha = 0.25f),
                radius = radius * 1.35f,
                style = Stroke(width = 3.dp.toPx())
            )

            // Middle Tech Arc Ring
            drawCircle(
                color = primaryColor.copy(alpha = 0.5f),
                radius = radius * 1.15f,
                style = Stroke(width = 5.dp.toPx())
            )

            // Glowing Core Orb Gradient
            drawCircle(
                brush = Brush.radialGradient(
                    colors = listOf(
                        Color.White,
                        primaryColor,
                        primaryColor.copy(alpha = 0.4f),
                        Color.Transparent
                    ),
                    center = center,
                    radius = radius
                ),
                radius = radius
            )
        }
    }
}
