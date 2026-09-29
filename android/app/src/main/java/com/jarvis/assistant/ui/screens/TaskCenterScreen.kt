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
import com.jarvis.assistant.viewmodel.UiTask

@Composable
fun TaskCenterScreen(viewModel: JarvisViewModel) {
    val tasks by viewModel.tasks.collectAsState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ObsidianBg)
            .padding(16.dp)
    ) {
        Text(
            text = "Task Center & Operations",
            color = NeonCyan,
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold
        )
        Text(
            text = "Autonomous coding and background execution pipeline",
            color = TextMuted,
            fontSize = 12.sp
        )

        Spacer(modifier = Modifier.height(16.dp))

        if (tasks.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .weight(1f),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "No active tasks in queue. Say 'JARVIS, build me a module' to begin.",
                    color = TextSecondary,
                    fontSize = 14.sp
                )
            }
        } else {
            LazyColumn(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                items(tasks) { task ->
                    TaskCard(task = task, onCancel = { viewModel.cancelActiveTask(task.id) })
                }
            }
        }
    }
}

@Composable
fun TaskCard(task: UiTask, onCancel: () -> Unit) {
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
                    text = task.title,
                    color = TextPrimary,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold
                )
                val statusColor = when (task.status) {
                    "COMPLETED" -> NeonCyan
                    "FAILED", "CANCELLED" -> CriticalCrimson
                    "RECTIFYING" -> WarningAmber
                    else -> ElectricBlue
                }
                Text(
                    text = task.status,
                    color = statusColor,
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold
                )
            }

            task.currentStep?.let { step ->
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Step: $step",
                    color = TextSecondary,
                    fontSize = 12.sp
                )
            }

            if (task.status in listOf("PLANNING", "IMPLEMENTING", "TESTING", "RECTIFYING")) {
                Spacer(modifier = Modifier.height(10.dp))
                Button(
                    onClick = onCancel,
                    colors = ButtonDefaults.buttonColors(containerColor = CriticalCrimson.copy(alpha = 0.2f)),
                    shape = RoundedCornerShape(8.dp),
                    contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                ) {
                    Text("HALT TASK", color = CriticalCrimson, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}
