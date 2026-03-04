// Polyfill ErrorUtils if not defined (fixes HMRClient.setup crash on some devices)
if (typeof globalThis.ErrorUtils === 'undefined') {
  globalThis.ErrorUtils = {
    reportFatalError: function(error) {
      console.error(error);
    },
    setGlobalHandler: function() {},
    getGlobalHandler: function() { return function() {}; },
  };
}

const { registerRootComponent } = require("expo");
const { default: App } = require("./App");

registerRootComponent(App);
