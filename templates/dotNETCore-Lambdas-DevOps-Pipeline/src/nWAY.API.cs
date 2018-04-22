using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel;

using Amazon.Lambda.Core;
using Amazon.Lambda.APIGatewayEvents;
using Newtonsoft.Json;

using nWAY.Library;
using nWAY.Library.SOAP;
using System.Reflection;

// Assembly attribute to enable the Lambda function's JSON input to be converted into a .NET class.
[assembly: LambdaSerializer(typeof(Amazon.Lambda.Serialization.Json.JsonSerializer))]
namespace nWAY
{
    public class API
    {

        /* SOAP Proxy  */
        [AWSApiGatewayProperties(Path:"MapMEWebServices.asmx")]
        public APIGatewayProxyResponse SOAPProxy(APIGatewayProxyRequest Request, ILambdaContext context){

            try{ 
                SOAPFunctionDefinition functionDefinition = SOAPFunctionDefinition.ParseXMLEnvelopeCall(Request.Body);
                
                SOAPFunctions soapFunctions = new SOAPFunctions();
                var result = soapFunctions.GetType().InvokeMember(functionDefinition.FunctionName, BindingFlags.InvokeMethod, null, soapFunctions, functionDefinition.FunctionAttributes.Cast<Object>().ToArray());
                return new APIGatewayProxyResponse{
                    StatusCode = 200,
                    Headers =  new Dictionary<string,string>(){{"Content-Type","text/xml"}},
                    Body = SOAPFunctionDefinition.CreateSOAPResponse(functionDefinition.FunctionName, (string)result)
                };
            }catch(Exception e){
                return APIGatewayProxyResponses.UnexpectedError(e);
            }
        }

        /* A function to check if our API is up and running. */
        public APIGatewayProxyResponse CheckStatus(APIGatewayProxyRequest Request, ILambdaContext context) => new APIGatewayProxyResponse
        {
            StatusCode = 200,
            Headers =  new Dictionary<string,string>(){{"Content-Type","text/plain"}},
            Body = String.Format("Running lambda version {0} {1}.", context.FunctionVersion, JsonConvert.SerializeObject(Request?.StageVariables))
        };


        /* A function to get caller IP displayed. */
        public APIGatewayProxyResponse MyIP(APIGatewayProxyRequest Request, ILambdaContext context) => new APIGatewayProxyResponse
        {
            StatusCode = 200,
            Headers =  new Dictionary<string,string>(){{"Content-Type","text/plain"}},
            Body = Request.RequestContext?.Identity?.SourceIp ?? "undefined"
        };
    }
}
