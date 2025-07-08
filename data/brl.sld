<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:gml="http://www.opengis.net/gml" version="1.0.0" xmlns:ogc="http://www.opengis.net/ogc">
  <UserLayer>
    <sld:LayerFeatureConstraints>
      <sld:FeatureTypeConstraint/>
    </sld:LayerFeatureConstraints>
    <sld:UserStyle>
      <sld:Name>difhead</sld:Name>
      <sld:FeatureTypeStyle>
        <sld:Rule>
          <sld:RasterSymbolizer>
            <sld:ChannelSelection>
              <sld:GrayChannel>
                <sld:SourceChannelName>1</sld:SourceChannelName>
              </sld:GrayChannel>
            </sld:ChannelSelection>
            <sld:ColorMap type="ramp" extended="true">
              <sld:ColorMapEntry quantity="-1000" label="Verschil in grondwaterstand (in m)" color="#7a0402" opacity="0.01"/>
              <sld:ColorMapEntry quantity="-1" label="-1" color="#7a0402"/>
              <sld:ColorMapEntry quantity="-0.750" label="-0.75" color="#d02f04"/>
              <sld:ColorMapEntry quantity="-0.50" label="-0.25" color="#fa7d20"/>
              <sld:ColorMapEntry quantity="-0.25" label="-0.125" color="#edcf39"/>
              <sld:ColorMapEntry quantity="-0.00" label="-0.00" color="#a1fc3d" opacity="0.01"/>
              <sld:ColorMapEntry quantity="0.25" label="0.125" color="#2ff09a"/>
              <sld:ColorMapEntry quantity="0.50" label="0.25" color="#2ab9ed"/>
              <sld:ColorMapEntry quantity="0.75" label="0.75" color="#4668e0"/>
              <sld:ColorMapEntry quantity="1000" label="1" color="#0000ff"/>
            </sld:ColorMap>
          </sld:RasterSymbolizer>
        </sld:Rule>
      </sld:FeatureTypeStyle>
    </sld:UserStyle>
  </UserLayer>
</StyledLayerDescriptor>
