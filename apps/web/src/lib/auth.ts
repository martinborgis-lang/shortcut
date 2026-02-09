import { auth } from '@clerk/nextjs'

export async function getAuthToken() {
  const { getToken } = auth()
  return await getToken()
}

export function withAuth<T extends Record<string, any>>(
  handler: (params: T & { userId: string }) => Promise<Response>
) {
  return async (params: T): Promise<Response> => {
    const { userId } = auth()

    if (!userId) {
      return new Response('Unauthorized', { status: 401 })
    }

    return handler({ ...params, userId })
  }
}