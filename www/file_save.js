/**
 * TODO(developer): Uncomment the following lines before running the sample.
 */
// The ID of your GCS bucket


  
function cloudConnect(data) {
    const bucketName = '134197212093-j7ocqjelna2il5osp0b4hp36hmmv9rqk.apps.googleusercontent.com';

    // The path to your file to upload
    var filePath = data["attachments"];
    
    // The new ID for your GCS file
    var destFileName = data["title"] + "_" + data["email"] + "_" + data["attachments"] + "_" + data["datetime"];
    
    // Imports the Google Cloud client library
    const {Storage} = require('@google-cloud/storage');
    
    // Creates a client
    const storage = new Storage();
    
    async function uploadFile() {
      await storage.bucket(bucketName).upload(filePath, {
        destination: destFileName,
      });
    
      console.log(`${filePath} uploaded to ${bucketName}`);
    }
    
    uploadFile().catch(console.error);
}