import * as Minio from 'minio'

export const minioClient = new Minio.Client({
  endPoint: process.env.MINIO_ENDPOINT!,
  port: parseInt(process.env.MINIO_PORT!),
  useSSL: process.env.MINIO_USE_SSL === 'true',
  accessKey: process.env.MINIO_ACCESS_KEY!,
  secretKey: process.env.MINIO_SECRET_KEY!,
})

export const BUCKET = process.env.MINIO_BUCKET!

export async function ensureBucket() {
  const exists = await minioClient.bucketExists(BUCKET)
  if (!exists) await minioClient.makeBucket(BUCKET, 'eu-west-1')
}

export async function getPresignedUploadUrl(objectName: string): Promise<string> {
  return minioClient.presignedPutObject(BUCKET, objectName, 15 * 60)
}

export async function getPresignedDownloadUrl(objectName: string): Promise<string> {
  return minioClient.presignedGetObject(BUCKET, objectName, 60 * 60)
}
