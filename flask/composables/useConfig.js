export async function useConfig() {
  return await useState('config').value.then(r => r);
}
