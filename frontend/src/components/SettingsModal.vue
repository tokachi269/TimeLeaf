<template>
  <div v-if="show" class="modal">
    <div class="modal-content">
      <span class="close" @click="close">&times;</span>
      <p>設定</p>
      <div class="setting-container">
        <div class="switch-container">
          <label class="switch"
            :style="{ '--switch-width': switchWidth, '--switch-height': switchHeight || `calc(${switchWidth} * 0.56)` }">
            <input type="checkbox" v-model="isDarkMode" @change="toggleSetting('darkMode', isDarkMode)">
            <span class="slider round"></span>
          </label>
          <span>ダークモード</span>
        </div>
        <br>
        <!-- <div class="switch-container">
          <label class="switch" :style="{ '--switch-width': '45px', '--switch-height': '25px' }">
            <input type="checkbox" v-model="isSmallSwitch" @change="toggleSetting('smallSwitch', isSmallSwitch)">
            <span class="slider round"></span>
          </label>
          <span>小さいスイッチ</span>
        </div> -->
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    show: {
      type: Boolean,
      required: true
    },
    switchWidth: {
      type: String,
      default: '60px'
    },
    switchHeight: {
      type: String,
      default: ''
    }
  },
  data() {
    return {
      isDarkMode: false,
      isSmallSwitch: false
    };
  },
  methods: {
    close() {
      this.$emit('close');
    },
    toggleSetting(settingName, value) {
      console.log("toggleSetting：" + `toggle-${settingName}`);
      localStorage.setItem(settingName, value);
      this.$emit(`toggle-${settingName}`, value);
    }
  },
  mounted() {
    this.isDarkMode = localStorage.getItem('darkMode') === 'true';
    this.isSmallSwitch = localStorage.getItem('smallSwitch') === 'true';
  }
}
</script>

<style scoped>
.modal {
  display: flex;
  justify-content: center;
  align-items: center;
  position: fixed;
  z-index: 1000;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  overflow: auto;
  background-color: rgba(0, 0, 0, 0.4);
}

.modal-content {
  background-color: var(--modal-background-color);
  padding: 20px;
  border: 1px solid #888;
  width: 80%;
  max-width: 500px;
  border-radius: 10px;
}

.close {
  color: #aaa;
  float: right;
  font-size: 28px;
  font-weight: bold;
}

.close:hover,
.close:focus {
  color: black;
  text-decoration: none;
  cursor: pointer;
}

.setting-container {
  display: flex;
  flex-direction: column;
  margin-bottom: 10px;
}

.switch-container {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.switch {
  position: relative;
  display: inline-block;
  width: var(--switch-width, 60px);
  height: var(--switch-height, calc(var(--switch-width, 60px) * 0.56));
  margin-right: 10px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: calc(var(--switch-height, calc(var(--switch-width, 60px) * 0.56)) / 2);
}

.slider:before {
  position: absolute;
  content: "";
  height: calc(var(--switch-height, calc(var(--switch-width, 60px) * 0.56)) - 8px);
  width: calc(var(--switch-height, calc(var(--switch-width, 60px) * 0.56)) - 8px);
  left: 4px;
  bottom: 4px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked+.slider {
  background-color: var(--button-active-background-color);
}

input:checked+.slider:before {
  transform: translateX(calc(var(--switch-width, 60px) - var(--switch-height, calc(var(--switch-width, 60px) * 0.56))));
}
</style>