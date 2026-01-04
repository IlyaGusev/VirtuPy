export default [
  {
    files: ["gui/**/*.js"],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: "module",
      globals: {
        window: "readonly",
        document: "readonly",
        console: "readonly",
        fetch: "readonly",
        WebSocket: "readonly",
        Blob: "readonly",
        URL: "readonly",
        location: "readonly",
        PIXI: "readonly"
      }
    },
    rules: {
      "no-unused-vars": ["warn", { "caughtErrors": "none" }],
      "no-undef": "error",
      "semi": ["error", "always"]
    }
  }
];
