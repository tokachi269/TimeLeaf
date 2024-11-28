const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    https: true,
  },
  configureWebpack: {
    devtool: 'source-map'
  },

})
