const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  filenameHashing: true,
  transpileDependencies: true,
  devServer: {
    https: true,
  },
  configureWebpack: {
    devtool: 'source-map'
  },
  pages: {
    index: {
      entry: 'src/main.js', // ここは変えないで
      title: 'TimeLeaf', // 好きな文字列をいれてください
    }
  },
  assetsDir: 'static',
})
