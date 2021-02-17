const off = 'off';
const warn = 'warn';
const error = 'error';

module.exports = {
  extends: 'makina',
  parser: 'babel-eslint',
  parserOptions: {
    sourceType: 'module',
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
    'no-use-before-define': [warn],
    'max-len': [1, 500, 4]
  },
};

