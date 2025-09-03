// uno.config.ts
import { defineConfig } from "unocss";
import { presetWind3 } from "@unocss/preset-wind3"; // ✅ 新预设

export default defineConfig({
  presets: [
    presetWind3(), // ✅ 使用新预设
  ],
  include: [/\.tsx?$/, /\.vue$/, /index\.html$/],
  theme: {
    colors: {
      primary: "#007bff",
      success: "#28a745",
      danger: "#dc3545",
    },
  },
});
