const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    host: '0.0.0.0',
    port: 8080,
    allowedHosts: 'all',
    client: {
      webSocketURL: {
        hostname: 'a119-59-6-44-201.ngrok-free.app',  // ngrok 주소
        protocol: 'wss',
        port: 443
      }
    }
  }
})
