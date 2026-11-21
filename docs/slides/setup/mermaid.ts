import { defineMermaidSetup } from '@slidev/types'

export default defineMermaidSetup(() => {
  return {
    theme: 'forest',
    flowchart: {
      curve: 'basis',
      padding: 16,
    },
  }
})