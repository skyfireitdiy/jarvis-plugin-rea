// 侧边栏视图组件模板（可选，需在 config.yaml 的 frontend.sidebar_views 声明）
// 约定：纯浏览器 ES module，用 window.Vue 渲染，导出 default 组件，不要 import 'vue'。
export default {
  name: "PluginSidebarView",
  template: `
    <div style="padding: 16px;">
      <h3>插件视图</h3>
      <p>在此实现侧边栏视图内容。</p>
    </div>
  `,
};
