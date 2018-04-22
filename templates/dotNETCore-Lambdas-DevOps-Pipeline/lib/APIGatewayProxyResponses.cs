using System;
using System.Collections.Generic;

using Amazon.Lambda.Core;
using Amazon.Lambda.APIGatewayEvents;

namespace nWAY.Library {

    public class APIGatewayProxyResponses {

        public static APIGatewayProxyResponse UnexpectedError(Exception e) => new APIGatewayProxyResponse{
                    StatusCode = 500,
                    Headers =  new Dictionary<string,string>(){{"Content-Type","text/plain"}},
                    Body = e?.Message ?? "unexpected error"
        };
    }
}