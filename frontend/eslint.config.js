import js from '@eslint/js'
import jsdoc from 'eslint-plugin-jsdoc'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import globals from 'globals'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist', 'node_modules', 'coverage'] },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: { ecmaVersion: 2023, globals: globals.browser },
    plugins: { 'react-hooks': reactHooks, 'react-refresh': reactRefresh, jsdoc },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      // Documentation standard (docs/DOCUMENTATION.md): every exported function, class and
      // arrow component carries TSDoc.
      'jsdoc/require-jsdoc': [
        'error',
        {
          publicOnly: true,
          require: { FunctionDeclaration: true, ClassDeclaration: true, ArrowFunctionExpression: true },
        },
      ],
    },
  },
  {
    // shadcn-generated primitives, tests and tool configs are exempt from the TSDoc rule.
    files: ['src/components/ui/**', '**/*.test.{ts,tsx}', 'src/test/**', '*.config.ts', 'src/main.tsx'],
    rules: { 'jsdoc/require-jsdoc': 'off', 'react-refresh/only-export-components': 'off' },
  },
)
