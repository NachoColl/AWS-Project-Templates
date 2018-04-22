using System;

namespace nWAY.Library
{
    [AttributeUsage(AttributeTargets.Method, AllowMultiple = false)]
    public class AWSApiGatewayProperties : Attribute {
        public string Path { get; set; } 

        public AWSApiGatewayProperties(string Path){ 
            this.Path = Path;
        }
    }
}
