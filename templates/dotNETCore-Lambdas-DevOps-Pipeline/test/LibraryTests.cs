using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using Xunit;
using Amazon.Lambda.Core;
using Amazon.Lambda.APIGatewayEvents;
using Amazon.Lambda.TestUtilities;

using nWAY.Library.SOAP;
using System.IO;

namespace nWAY.Tests
{
    public class LibraryTests
    {
        [Fact]
        public void TestSimpleSoapParsing()
        {
            string soapMessage = File.ReadAllText(@"./soapMessage1.xml");
            SOAPFunctionDefinition result = SOAPFunctionDefinition.ParseXMLEnvelopeCall(soapMessage);

            Assert.Equal("CheckStatus", result.FunctionName);
            Assert.Equal(1, result.FunctionAttributes.Count());
            Assert.Equal("string", result.FunctionAttributes[0]);
        }

    
    }
}
