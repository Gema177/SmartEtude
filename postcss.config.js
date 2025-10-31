module.exports = {
  plugins: {
    // =============================================================================
    // PLUGINS POSTCSS PRINCIPAUX
    // =============================================================================
    
    // Tailwind CSS - Framework CSS utilitaire
    tailwindcss: {},
    
    // Autoprefixer - Ajoute automatiquement les préfixes navigateur
    autoprefixer: {
      flexbox: 'no-2009',
      grid: 'autoplace',
    },
    
    // =============================================================================
    // PLUGINS OPTIONNELS (décommentez selon vos besoins)
    // =============================================================================
    
    // PostCSS Preset Env - Utilise les fonctionnalités CSS modernes
    // 'postcss-preset-env': {
    //   stage: 3,
    //   features: {
    //     'nesting-rules': true,
    //     'custom-media-queries': true,
    //     'media-query-ranges': true,
    //   },
    // },
    
    // CSSNano - Minification CSS (production uniquement)
    // 'cssnano': process.env.NODE_ENV === 'production' ? {
    //   preset: ['default', {
    //     discardComments: {
    //       removeAll: true,
    //     },
    //     normalizeWhitespace: true,
    //   }],
    // } : false,
    
    // PostCSS Import - Permet d'importer des fichiers CSS
    // 'postcss-import': {},
    
    // PostCSS Nested - Support de la syntaxe nested
    // 'postcss-nested': {},
    
    // PostCSS Custom Properties - Support des variables CSS
    // 'postcss-custom-properties': {
    //   preserve: false,
    //   importFrom: [
    //     {
    //       customProperties: {
    //         '--primary-color': '#3b82f6',
    //         '--secondary-color': '#7c3aed',
    //         '--accent-color': '#10b981',
    //       },
    //     },
    //   ],
    // },
  },
}
