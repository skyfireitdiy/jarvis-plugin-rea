// 管理页 Tab 组件模板（可选，需在 config.yaml 的 frontend.admin_tabs 声明）
// 约定：纯浏览器 ES module，用 window.Vue 渲染，导出 default 组件，不要 import 'vue'。
export default {
  name: "PluginAdminTab",
  template: `
    <div style="padding: 16px;">
      <h3>插件管理页</h3>
      <p>在此实现管理功能。</p>
    </div>
  `,
};
