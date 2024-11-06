<template>
  <div id="app">
    <h1>Code: {{ code }}</h1>
    <img alt="Vue logo" src="./assets/logo.png" />
    <HelloWorld msg="Welcome to Your Vue.js App" />
    <TimelineView :code = "code" />
  </div>
</template>

<script>
import HelloWorld from './components/HelloWorld.vue'
import TimelineView from './views/TimelineView.vue'

export default {
  name: 'App',
  components: {
    HelloWorld,
    TimelineView,
  },
  computed: {
    code() {
      const code = this.$route.query.code;
      console.log('Code in App.vue:', code); // ここで確認
      return this.$route.query.code;  // パスパラメーター `id` を取得
    },
  },
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>