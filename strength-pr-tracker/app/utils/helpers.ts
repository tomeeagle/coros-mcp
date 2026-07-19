export function slugify(str: string) {
  str = str.replace(/^\s+|\s+$/g, ''); // trim leading/trailing white space
  str = str.toLowerCase(); // convert string to lowercase
  str = str
    .replace(/[^a-z0-9 -]/g, '') // remove any non-alphanumeric characters
    .replace(/\s+/g, '-') // replace spaces with hyphens
    .replace(/-+/g, '-'); // remove consecutive hyphens
  return str;
}

export function unslugify(slug: string) {
  slug = slug.replace(/^\s+|\s+$/g, ''); // trim leading/trailing white space
  slug = slug.replace(/-/g, ' '); // replace hyphens with spaces
  slug = slug
    .replace(/[^a-z0-9 ]/g, '') // remove any non-alphanumeric characters
    .replace(/\s+/g, ' ') // replace spaces with hyphens
    .replace(/ +/g, ' ') // remove consecutive spaces
    .split(' ')
    .map((word) => {
      return word.charAt(0).toUpperCase() + word.slice(1);
    })
    .join(' ');
  return slug;
}
