/** Strips Markdown syntax for short plain-text previews. */
export function stripMarkdown(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, '[code]')
    .replace(/^\s*\|?[-:| ]+\|[-:| ]*$/gm, '')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/(\*\*|__|\*|_|`)/g, '')
    .replace(/\|/g, ' ')
    .replace(/\n{2,}/g, '\n')
    .trim()
}
