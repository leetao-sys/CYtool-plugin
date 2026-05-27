<template>
  <el-container class="app-shell">
    <el-aside width="280px" class="sidebar">
      <div class="brand">
        <div class="brand-mark">CY</div>
        <div>
          <h1>CYtool</h1>
          <p>插件工具控制台</p>
        </div>
      </div>

      <div class="sidebar-section">
        <div class="sidebar-label">平台</div>
        <el-menu :default-active="active" class="side-menu" @select="active = $event">
          <el-menu-item index="manage">
            <span class="menu-dot manage-dot"></span>
            <span>插件管理</span>
          </el-menu-item>
        </el-menu>
      </div>

      <div class="sidebar-section plugin-menu-section">
        <div class="sidebar-label">已启用插件</div>
        <el-empty v-if="menus.length === 0" description="暂无插件" :image-size="72" />
        <el-menu v-else :default-active="active" class="side-menu" @select="active = $event">
          <el-menu-item
            v-for="item in menus"
            :key="item.plugin_id"
            :index="item.plugin_id"
          >
            <span class="menu-dot"></span>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </el-menu>
      </div>
    </el-aside>

    <el-main class="main">
      <PluginManager v-if="active === 'manage'" @changed="refresh" />
      <section v-else class="plugin-page">
        <div class="plugin-page-header">
          <div>
            <p class="eyebrow">插件运行</p>
            <h2>{{ currentPlugin?.title }}</h2>
          </div>
          <el-button @click="active = 'manage'">返回管理</el-button>
        </div>
        <iframe
          class="plugin-frame"
          :src="currentPlugin?.frontend_url"
          title="plugin"
        />
      </section>
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import PluginManager from './components/PluginManager.vue'
import { getMenus, type PluginMenu } from './services/api'

const active = ref('manage')
const menus = ref<PluginMenu[]>([])
const currentPlugin = computed(() => menus.value.find(item => item.plugin_id === active.value))

async function refresh() {
  menus.value = await getMenus()
  if (active.value !== 'manage' && !currentPlugin.value) active.value = 'manage'
}

onMounted(refresh)
</script>
