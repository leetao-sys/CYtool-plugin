<template>
  <section class="panel">
    <div class="toolbar">
      <h1>插件管理</h1>
      <input type="file" accept=".zip" @change="upload" />
    </div>
    <el-table :data="plugins" border>
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="version" label="版本" width="100" />
      <el-table-column prop="status" label="状态" width="110" />
      <el-table-column prop="description" label="描述" />
      <el-table-column label="操作" width="260">
        <template #default="{ row }">
          <el-button size="small" @click="toggle(row)">
            {{ row.status === 'enabled' ? '禁用' : '启用' }}
          </el-button>
          <el-button size="small" type="danger" @click="remove(row.id)">卸载</el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { disablePlugin, enablePlugin, getPlugins, removePlugin, uploadPlugin, type PluginInfo } from '../services/api'

const emit = defineEmits<{ changed: [] }>()
const plugins = ref<PluginInfo[]>([])

async function refresh() {
  plugins.value = await getPlugins()
  emit('changed')
}

async function upload(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    await uploadPlugin(file)
    ElMessage.success('插件安装成功')
    await refresh()
  } finally {
    input.value = ''
  }
}

async function toggle(plugin: PluginInfo) {
  if (plugin.status === 'enabled') await disablePlugin(plugin.id)
  else await enablePlugin(plugin.id)
  await refresh()
}

async function remove(id: string) {
  await removePlugin(id)
  await refresh()
}

onMounted(refresh)
</script>
