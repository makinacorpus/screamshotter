const off = 'off';
const warn = 'warn';
const error = 'error';
const always = 'always';

module.exports = {
  extends: 'airbnb-base',
  parser: '@babel/eslint-parser',
  parserOptions: {
    ecmaVersion: "latest",
    requireConfigFile: false,
  },
  env: {
    browser: true,
    jest: true,
  },
  globals: {
  },
  rules: {
    'func-names':           [off],
    'no-console':           [off],
    'no-param-reassign':    [off],
    'no-underscore-dangle': [off],
    'no-case-declarations': [off],
    strict:                 [off],
    'global-require': [warn],
    'max-len': [1, 500, 4],
    'arrow-parens':                      [error, 'as-needed'],
    camelcase:                           [warn],
    'object-curly-newline':              [warn, { consistent: true }],
    'implicit-arrow-linebreak':          [off],
    'prefer-template':                   [warn],
    'space-before-function-paren':       [error, always],

    'import/extensions':                 [warn],
    'import/no-extraneous-dependencies': [warn, { devDependencies: ['**/*.test.js', '**/*.spec.js', '**/*.stories.js'] }],
    'import/no-named-as-default':        [off],
    'import/no-unresolved':              [warn],

    'key-spacing': [error, {
      singleLine: { mode: 'strict' },
      multiLine:  { mode: 'minimum' },
    }],

    'no-multi-spaces': [warn, {
      exceptions: {
        Property:           true,
        VariableDeclarator: true,
        ImportDeclaration:  true,
        BinaryExpression:   true,
      },
    }],

    'no-unused-expressions': [warn, {
      allowShortCircuit:    true,
      allowTernary:         true,
      allowTaggedTemplates: true,
    }],
  },
};
