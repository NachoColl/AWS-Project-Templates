using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using Xunit;
using Amazon.Lambda.Core;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.Lambda.TestUtilities;

using nWAY;
using System.IO;
using nWAY.Library.SOAP;

namespace nWAY.Tests
{
    public class APITests
    {
        nWAY.API nWAYAPI = new nWAY.API();
        TestLambdaContext context = new TestLambdaContext();

        [Fact]
        public void TestCheckStatus()
        {
            APIGatewayProxyResponse status = nWAYAPI.CheckStatus(Request: new Amazon.Lambda.APIGatewayEvents.APIGatewayProxyRequest(){ Body = "Hello world"}, context: context);
            Assert.Equal(200, status.StatusCode);
        }

        [Fact]
        public void TestCheckMyIp()
        {
            APIGatewayProxyResponse status = nWAYAPI.MyIP(Request: new Amazon.Lambda.APIGatewayEvents.APIGatewayProxyRequest(){ Body = "Hello world"}, context: context);
            Assert.Equal(200, status.StatusCode);
        }

        [Fact]
        public void SOAP_CheckStatus()
        {
            string soapMessage = File.ReadAllText(@"./soapMessage1.xml");
            APIGatewayProxyResponse status = nWAYAPI.SOAPProxy(Request: new Amazon.Lambda.APIGatewayEvents.APIGatewayProxyRequest(){ Body = soapMessage}, context: context);
           
            string soapMessageResponse = File.ReadAllText(@"./soapMessage1_Result.xml");
            Assert.Equal(200, status.StatusCode);
            Assert.Equal(soapMessageResponse, status.Body, true, true, true);
        }
    }
}
